import { create } from "zustand";
import { ScannerStatus, opportunitiesApi } from "./api";

interface ScannerStore {
  status: ScannerStatus | null;
  refreshKey: number;
  _polling: boolean;
  startPolling: () => void;
  stopPolling: () => void;
}

let _intervalId: ReturnType<typeof setInterval> | null = null;

export const useScannerStore = create<ScannerStore>((set, get) => ({
  status: null,
  refreshKey: 0,
  _polling: false,

  startPolling: () => {
    if (get()._polling) return;
    set({ _polling: true });

    let lastScanId: number | null | undefined = undefined;

    const check = async () => {
      try {
        const status = await opportunitiesApi.scannerStatus();
        const newScan =
          lastScanId !== undefined && status.last_scan_id !== lastScanId;
        if (newScan) {
          set((s) => ({ status, refreshKey: s.refreshKey + 1 }));
        } else {
          set({ status });
        }
        lastScanId = status.last_scan_id;
      } catch {}
    };

    check();
    _intervalId = setInterval(check, 10_000);
  },

  stopPolling: () => {
    if (_intervalId) {
      clearInterval(_intervalId);
      _intervalId = null;
    }
    set({ _polling: false });
  },
}));
