import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ExtractorState, ProcessOptions, RunHistory, Language } from '@/lib/types';
import { getCurrentLanguage, setLanguage } from '@/lib/i18n';

interface ExtractorStore extends ExtractorState {
  // Actions
  setFiles: (files: File[]) => void;
  addFiles: (files: File[]) => void;
  removeFile: (index: number) => void;
  clearFiles: () => void;
  setOptions: (options: Partial<ProcessOptions>) => void;
  setLanguage: (language: Language) => void;
  startRun: (runId: string) => void;
  updateProgress: (progress: number, stage?: string, message?: string) => void;
  addLog: (log: string) => void;
  completeRun: () => void;
  errorRun: (error: string) => void;
  resetRun: () => void;
  addToHistory: (run: RunHistory) => void;
  clearHistory: () => void;
}

const defaultOptions: ProcessOptions = {
  apply_filter: false,
  verbose: false,
  language: 'gr', // Always start with Greek to prevent hydration mismatch
};

export const useExtractorStore = create<ExtractorStore>()(
  persist(
    (set, get) => ({
      // Initial state
      files: [],
      options: defaultOptions,
      run: {
        status: 'idle',
        progress: 0,
        logs: [],
      },
      history: [],

      // File actions
      setFiles: (files) => set({ files }),

      addFiles: (newFiles) => {
        const currentFiles = get().files;
        const combined = [...currentFiles, ...newFiles];
        set({ files: combined });
      },

      removeFile: (index) => {
        const files = get().files;
        const newFiles = files.filter((_, i) => i !== index);
        set({ files: newFiles });
      },

      clearFiles: () => set({ files: [] }),

      // Options actions
      setOptions: (newOptions) => {
        const currentOptions = get().options;
        const updatedOptions = { ...currentOptions, ...newOptions };
        set({ options: updatedOptions });
      },

      setLanguage: (language) => {
        setLanguage(language);
        set((state) => ({
          options: { ...state.options, language },
        }));
      },

      // Run actions
      startRun: (runId) => {
        set({
          run: {
            id: runId,
            status: 'running',
            progress: 0,
            stage: undefined,
            message: undefined,
            logs: [],
          },
        });
      },

      updateProgress: (progress, stage, message) => {
        set((state) => ({
          run: {
            ...state.run,
            progress,
            stage,
            message,
          },
        }));
      },

      addLog: (log) => {
        set((state) => ({
          run: {
            ...state.run,
            logs: [...state.run.logs, log],
          },
        }));
      },

      completeRun: () => {
        set((state) => ({
          run: {
            ...state.run,
            status: 'done',
            progress: 100,
          },
        }));
      },

      errorRun: (error) => {
        set((state) => ({
          run: {
            ...state.run,
            status: 'error',
            message: error,
          },
        }));
      },

      resetRun: () => {
        set({
          run: {
            status: 'idle',
            progress: 0,
            logs: [],
          },
        });
      },

      // History actions
      addToHistory: (run) => {
        const history = get().history;
        const newHistory = [run, ...history].slice(0, 5); // Keep only last 5
        set({ history: newHistory });
      },

      clearHistory: () => set({ history: [] }),
    }),
    {
      name: 'dei-extractor-store',
      partialize: (state) => ({
        options: state.options,
        history: state.history,
      }),
    }
  )
);
