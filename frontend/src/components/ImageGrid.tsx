import type { ImageResult } from "../lib/types";
import ImageCard from "./ImageCard";

export default function ImageGrid({ images }: { images: ImageResult[] }) {
  if (images.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 dark:text-gray-400">
        검색 결과가 없습니다
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
      {images.map((image) => (
        <ImageCard key={image.id} image={image} />
      ))}
    </div>
  );
}
