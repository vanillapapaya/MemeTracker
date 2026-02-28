import Link from "next/link";
import { getImage } from "../../../lib/api";
import ImageGrid from "../../../components/ImageGrid";

export default async function ImageDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let image;
  try {
    image = await getImage(id);
  } catch {
    return (
      <div className="px-4 pt-8 text-center">
        <p className="text-gray-500">이미지를 찾을 수 없습니다</p>
        <Link href="/" className="text-blue-600 text-sm mt-2 inline-block">
          홈으로 돌아가기
        </Link>
      </div>
    );
  }

  const src = image.thumbnail_url || "/placeholder.svg";

  return (
    <div className="px-4 pt-4 pb-8 max-w-2xl mx-auto">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-4">
        <Link href="/" className="text-gray-500 hover:text-foreground">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
        </Link>
        <span className="text-sm text-gray-500">이미지 상세</span>
      </div>

      {/* 이미지 */}
      <div className="rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800 mb-4">
        <img src={src} alt={image.caption || "짤"} className="w-full" />
      </div>

      {/* 액션 */}
      <div className="flex gap-4 mb-6">
        <span className="text-sm text-gray-600 dark:text-gray-300">
          ♥ {image.like_count}
        </span>
        <a
          href={image.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-blue-600 hover:underline"
        >
          원본 보기 →
        </a>
      </div>

      {/* 정보 */}
      <div className="space-y-4 text-sm">
        <div>
          <h3 className="font-semibold text-gray-500 dark:text-gray-400 mb-1">정보</h3>
          <p>출처: {image.source}</p>
          {image.caption && <p className="text-gray-600 dark:text-gray-300 mt-1">{image.caption}</p>}
          {image.tags && image.tags.length > 0 && (
            <div className="flex gap-1.5 mt-2 flex-wrap">
              {image.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-0.5 text-xs rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300"
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* 작가 */}
        {image.creator && (
          <div>
            <h3 className="font-semibold text-gray-500 dark:text-gray-400 mb-1">작가</h3>
            <p>
              {image.creator.display_name || "알 수 없음"}
              {image.creator.is_verified && " ✓"}
            </p>
            {image.creator.twitter_handle && (
              <a
                href={`https://x.com/${image.creator.twitter_handle}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                @{image.creator.twitter_handle}
              </a>
            )}
          </div>
        )}
      </div>

      {/* 비슷한 짤 */}
      {image.similar_images.length > 0 && (
        <div className="mt-8">
          <h3 className="font-semibold text-gray-500 dark:text-gray-400 mb-3">비슷한 짤</h3>
          <ImageGrid images={image.similar_images} />
        </div>
      )}
    </div>
  );
}
