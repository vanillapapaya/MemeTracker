import { create } from "zustand";
import type { ImageResult } from "../lib/types";

interface SearchState {
  query: string;
  results: ImageResult[];
  total: number;
  hasMore: boolean;
  loading: boolean;
  setQuery: (query: string) => void;
  setResults: (results: ImageResult[], total: number, hasMore: boolean) => void;
  appendResults: (results: ImageResult[], hasMore: boolean) => void;
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

export const useSearchStore = create<SearchState>((set) => ({
  query: "",
  results: [],
  total: 0,
  hasMore: false,
  loading: false,
  setQuery: (query) => set({ query }),
  setResults: (results, total, hasMore) => set({ results, total, hasMore }),
  appendResults: (results, hasMore) =>
    set((state) => ({
      results: [...state.results, ...results],
      hasMore,
    })),
  setLoading: (loading) => set({ loading }),
  reset: () => set({ query: "", results: [], total: 0, hasMore: false, loading: false }),
}));
