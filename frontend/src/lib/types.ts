export interface Creator {
  id: string;
  display_name: string | null;
  twitter_handle: string | null;
  is_verified: boolean;
}

export interface ImageResult {
  id: string;
  thumbnail_url: string | null;
  source_url: string;
  source: string;
  tags: string[] | null;
  caption: string | null;
  like_count: number;
  view_count: number;
  creator: Creator | null;
}

export interface ImageDetail extends ImageResult {
  similar_images: ImageResult[];
}

export interface SearchResponse {
  results: ImageResult[];
  total: number;
  has_more: boolean;
}

export interface FeedItem {
  type: "image" | "ad";
  data: ImageResult;
}

export interface FeedResponse {
  items: FeedItem[];
  next_cursor: string | null;
}
