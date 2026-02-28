import SearchBar from "../components/SearchBar";
import ImageGrid from "../components/ImageGrid";
import { getTrendingFeed } from "../lib/api";
import type { ImageResult } from "../lib/types";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  let trendingImages: ImageResult[] = [];
  try {
    const feed = await getTrendingFeed(12);
    trendingImages = feed.items
      .filter((item) => item.type === "image")
      .map((item) => item.data);
  } catch {
    // API 미연결 시 빈 상태
  }

  return (
    <div className="px-4 pt-12 pb-8">
      {/* 로고 */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-foreground">MemeTracker</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          짤과 원작자를 연결하는 검색 엔진
        </p>
      </div>

      {/* 검색바 */}
      <SearchBar />

      {/* 인기 검색어 */}
      <div className="flex justify-center gap-2 mt-4 flex-wrap">
        {["무한도전", "드레이크", "리액션", "짤"].map((tag) => (
          <a
            key={tag}
            href={`/search?q=${encodeURIComponent(tag)}`}
            className="px-3 py-1 text-sm rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700"
          >
            #{tag}
          </a>
        ))}
      </div>

      {/* 인기 짤 */}
      {trendingImages.length > 0 && (
        <div className="mt-10">
          <h2 className="text-lg font-semibold mb-4">지금 뜨는 짤</h2>
          <ImageGrid images={trendingImages} />
        </div>
      )}

      {trendingImages.length === 0 && (
        <div className="mt-16 text-center text-gray-400 dark:text-gray-500">
          <p className="text-lg mb-2">아직 짤이 없습니다</p>
          <p className="text-sm">백엔드 서버를 시작하고 데이터를 추가해보세요</p>
        </div>
      )}
    </div>
  );
}
