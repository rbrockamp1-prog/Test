import { google } from "googleapis";

export interface Lead {
  company: string;
  role: string;
  bucket: string;
  resume: string;
  status: string;
  url: string;
  dateAdded: string;
  dateApplied: string;
  followUpDue: string;
  whyItFits: string;
  fitScore: string;
}

const SHEET_ID = process.env.GOOGLE_SHEET_ID!;
const TRACKER_TAB = process.env.TRACKER_TAB ?? "Tracker";

function getAuth() {
  const raw = process.env.GOOGLE_SERVICE_ACCOUNT_JSON;
  if (!raw) throw new Error("GOOGLE_SERVICE_ACCOUNT_JSON not set");
  const creds = JSON.parse(raw);
  return new google.auth.GoogleAuth({
    credentials: creds,
    scopes: ["https://www.googleapis.com/auth/spreadsheets"],
  });
}

export async function getLeads(): Promise<Lead[]> {
  const auth = getAuth();
  const sheets = google.sheets({ version: "v4", auth });
  const res = await sheets.spreadsheets.values.get({
    spreadsheetId: SHEET_ID,
    range: `${TRACKER_TAB}!A:K`,
  });
  const rows = res.data.values ?? [];
  if (rows.length < 2) return [];
  // skip header row
  return rows.slice(1).map((r) => ({
    company: r[0] ?? "",
    role: r[1] ?? "",
    bucket: r[2] ?? "",
    resume: r[3] ?? "",
    status: r[4] ?? "",
    url: r[5] ?? "",
    dateAdded: r[6] ?? "",
    dateApplied: r[7] ?? "",
    followUpDue: r[8] ?? "",
    whyItFits: r[9] ?? "",
    fitScore: r[10] ?? "",
  }));
}

export async function updateStatus(
  company: string,
  role: string,
  status: string,
  dateApplied?: string
): Promise<void> {
  const auth = getAuth();
  const sheets = google.sheets({ version: "v4", auth });
  const res = await sheets.spreadsheets.values.get({
    spreadsheetId: SHEET_ID,
    range: `${TRACKER_TAB}!A:E`,
  });
  const rows = res.data.values ?? [];
  let rowIndex = -1;
  for (let i = 1; i < rows.length; i++) {
    if (
      rows[i][0]?.trim().toLowerCase() === company.trim().toLowerCase() &&
      rows[i][1]?.trim().toLowerCase() === role.trim().toLowerCase()
    ) {
      rowIndex = i + 1; // 1-indexed
      break;
    }
  }
  if (rowIndex === -1) throw new Error("Lead not found");

  const updates: { range: string; values: string[][] }[] = [
    { range: `${TRACKER_TAB}!E${rowIndex}`, values: [[status]] },
  ];
  if (dateApplied) {
    updates.push({ range: `${TRACKER_TAB}!H${rowIndex}`, values: [[dateApplied]] });
  }

  await sheets.spreadsheets.values.batchUpdate({
    spreadsheetId: SHEET_ID,
    requestBody: {
      valueInputOption: "USER_ENTERED",
      data: updates,
    },
  });
}
