import Tracker from "@/components/tracker";

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Elizabeth&apos;s Job Tracker</h1>
            <p className="text-sm text-gray-500 mt-0.5">Climate · Public Health · Emergency Management</p>
          </div>
          <div className="text-xs text-gray-400">Synced with Google Sheets</div>
        </div>
      </header>
      <div className="max-w-6xl mx-auto px-6 py-8">
        <Tracker />
      </div>
    </main>
  );
}
