import Link from "next/link";
import type { ImageResult } from "../lib/types";

export default function ImageCard({ image }: { image: ImageResult }) {
  const src = image.thumbnail_url || "/placeholder.svg";

  return (
    <Link href={`/image/${image.id}`} className="group block">
      <div className="relative aspect-square rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800">
        <img
          src={src}
          alt={image.caption || "짤"}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
          loading="lazy"
        />
      </div>
      <div className="mt-1.5 px-0.5">
        <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
          {image.source} {image.like_count > 0 && `· ♥ ${image.like_count}`}
        </p>
      </div>
    </Link>
  );
}
