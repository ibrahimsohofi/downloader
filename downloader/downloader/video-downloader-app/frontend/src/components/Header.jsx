export default function Header() {
  return (
    <header className="bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg">
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg
              className="w-10 h-10"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"
              />
            </svg>
            <div>
              <h1 className="text-3xl font-bold">Video Downloader</h1>
              <p className="text-sm text-blue-100">Download from multiple platforms</p>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-6">
            <div className="text-sm text-blue-100">
              <span className="font-semibold">Supports:</span> YouTube, SoundCloud & more
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
