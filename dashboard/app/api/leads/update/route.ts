import { NextRequest, NextResponse } from "next/server";
import { updateStatus } from "@/lib/sheets";

export async function POST(req: NextRequest) {
  try {
    const { company, role, status, dateApplied } = await req.json();
    if (!company || !role || !status) {
      return NextResponse.json({ error: "company, role, status required" }, { status: 400 });
    }
    await updateStatus(company, role, status, dateApplied);
    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error(err);
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}
