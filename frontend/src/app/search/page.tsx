"use client";

import { Suspense, useEffect, useCallback, useRef } from "react";
import { useSearchParams } from "next/navigation";
import SearchBar from "../../components/SearchBar";
import ImageGrid from "../../components/ImageGrid";
import { useSearchStore } from "../../store/useSearchStore";
import { searchImages } from "../../lib/api";

function SearchContent() {
  const searchParams = useSearchParams();
  const q = searchParams.get("q") || "";
  const { results, hasMore, loading, setResults, appendResults, setLoading, setQuery } =
    useSearchStore();
  const observerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!q) return;
    setQuery(q);
    setLoading(true);
    searchImages(q, 20, 0)
      .then((data) => {
        setResults(data.results, data.total, data.has_more);
      })
      .catch(() => {
        setResults([], 0, false);
      })
      .finally(() => setLoading(false));
  }, [q, setQuery, setResults, setLoading]);

  const loadMore = useCallback(() => {
    if (loading || !hasMore || !q) return;
    setLoading(true);
    searchImages(q, 20, results.length)
      .then((data) => {
        appendResults(data.results, data.has_more);
      })
      .finally(() => setLoading(false));
  }, [loading, hasMore, q, results.length, setLoading, appendResults]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) loadMore();
      },
      { threshold: 0.1 }
    );
    if (observerRef.current) observer.observe(observerRef.current);
    return () => observer.disconnect();
  }, [loadMore]);

  return (
    <div className="px-4 pt-4 pb-8">
      <SearchBar initialQuery={q} />

      {q && (
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-4 mb-4">
          &quot;{q}&quot; 검색 결과
        </p>
      )}

      {loading && results.length === 0 ? (
        <div className="text-center py-12 text-gray-400">검색 중...</div>
      ) : (
        <ImageGrid images={results} />
      )}

      {hasMore && <div ref={observerRef} className="h-10" />}
      {loading && results.length > 0 && (
        <div className="text-center py-4 text-gray-400 text-sm">불러오는 중...</div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="text-center py-12 text-gray-400">로딩 중...</div>}>
      <SearchContent />
    </Suspense>
  );
}
