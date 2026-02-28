import type { SearchResponse, ImageDetail, FeedResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchAPI<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
}

export async function searchImages(
  query: string,
  limit = 20,
  offset = 0,
  type = "all",
  source = "all"
): Promise<SearchResponse> {
  const params = new URLSearchParams({
    q: query,
    limit: String(limit),
    offset: String(offset),
    type,
    source,
  });
  return fetchAPI<SearchResponse>(`/search?${params}`);
}

export async function getImage(id: string): Promise<ImageDetail> {
  return fetchAPI<ImageDetail>(`/images/${id}`);
}

export async function getTrendingFeed(
  limit = 20,
  cursor?: string
): Promise<FeedResponse> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (cursor) params.set("cursor", cursor);
  return fetchAPI<FeedResponse>(`/feed/trending?${params}`);
}
