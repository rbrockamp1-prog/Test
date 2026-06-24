import { NextResponse } from "next/server";
import { getLeads } from "@/lib/sheets";

export const revalidate = 0; // no cache — always fresh

export async function GET() {
  try {
    const leads = await getLeads();
    return NextResponse.json(leads);
  } catch (err) {
    console.error(err);
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}
