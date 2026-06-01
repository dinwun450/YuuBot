"use client";

import dynamic from "next/dynamic";
import Image from "next/image";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useCopilotReadable } from "@copilotkit/react-core";
import { CopilotSidebar, useChatContext } from "@copilotkit/react-ui";

type TabId = "overview" | "japan" | "global" | "map" | "about";

type JapanQuakeRow = {
  date?: string | null;
  time?: string | null;
  location?: string | null;
  epicenter?: string | null;
  magnitude?: number | string | null;
  intensity?: string | null;
};

type GlobalQuakeRow = {
  date?: string | null;
  time?: string | null;
  magnitude?: number | string | null;
  location?: string | null;
  title?: string | null;
  tsunami?: boolean | string | null;
};

type JapanFilterState = {
  date: string;
  magnitude: string;
  intensity: string;
};

type GlobalFilterState = {
  date: string;
  magnitude: string;
  tsunami: string;
};

type QuakeSummary = {
  date: string;
  time: string;
  location: string;
  magnitude: string;
  intensity?: string;
  title?: string;
  tsunami?: boolean | string | null;
};

const QuakeMap = dynamic(
  () => import("@/components/quake-map").then((module) => module.QuakeMap),
  {
    ssr: false,
    loading: () => (
      <div className="quake-map-shell glassflow">
        <p className="quake-map-status">Loading map shell...</p>
      </div>
    ),
  },
);

function BlackChatButton() {
  const { open, setOpen, icons } = useChatContext();

  return (
    <button
      type="button"
      className="chat-fab"
      aria-label={open ? "Close chat" : "Open chat"}
      onClick={() => setOpen(!open)}
    >
      {open ? icons.closeIcon : icons.openIcon}
    </button>
  );
}

function normalizeQueryValue(value: unknown) {
  return String(value ?? "").toLowerCase().replace(/\s+/g, " ").trim();
}

function normalizeIntensityValue(intensity: string | null | undefined) {
  if (!intensity) return "";

  return intensity
    .trim()
    .replace(/^tbp/i, "")
    .replace(/å¼±/g, "-")
    .replace(/å¼·/g, "+")
    .replace(/[\sã€€]+/g, "");
}

function getShindoImage(intensity: string | null | undefined) {
  if (!intensity) return null;

  const normalized = normalizeIntensityValue(intensity);
  const shindoImageByIntensity: Record<string, string> = {
    "5-": "/shindo-images/tbp5弱.png",
    "5弱": "/shindo-images/tbp5弱.png",
    "5+": "/shindo-images/tbp5強.png",
    "5強": "/shindo-images/tbp5強.png",
    "6-": "/shindo-images/tbp6弱.png",
    "6弱": "/shindo-images/tbp6弱.png",
    "6+": "/shindo-images/tbp6強.png",
    "6強": "/shindo-images/tbp6強.png",
  };

  if (shindoImageByIntensity[normalized]) {
    return shindoImageByIntensity[normalized];
  }

  switch (normalized) {
    case "1":
      return "/shindo-images/tbp1.png";
    case "2":
      return "/shindo-images/tbp2.png";
    case "3":
      return "/shindo-images/tbp3.png";
    case "4":
      return "/shindo-images/tbp4.png";
    case "5-":
    case "5å¼±":
      return "/shindo-images/tbp5å¼±.png";
    case "5+":
    case "5å¼·":
      return "/shindo-images/tbp5å¼·.png";
    case "6-":
    case "6å¼±":
      return "/shindo-images/tbp6å¼±.png";
    case "6+":
    case "6å¼·":
      return "/shindo-images/tbp6å¼·.png";
    case "7":
      return "/shindo-images/tbp7.png";
    default:
      return null;
  }
}

function normalizeTsunamiValue(tsunami: boolean | string | null | undefined) {
  if (typeof tsunami === "boolean") {
    return tsunami ? "true" : "false";
  }

  if (typeof tsunami === "string") {
    const normalized = tsunami.trim().toLowerCase();
    if (["true", "yes", "1"].includes(normalized)) return "true";
    if (["false", "no", "0"].includes(normalized)) return "false";
  }

  return "";
}

function formatTsunamiValue(value: boolean | string | null | undefined) {
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    if (normalized === "true" || normalized === "yes") return "Yes";
    if (normalized === "false" || normalized === "no") return "No";
    return value;
  }

  return "-";
}

function compareQuakeTimeline(
  leftDate?: string | null,
  leftTime?: string | null,
  rightDate?: string | null,
  rightTime?: string | null,
) {
  const leftKey = `${leftDate ?? ""} ${leftTime ?? ""}`.trim();
  const rightKey = `${rightDate ?? ""} ${rightTime ?? ""}`.trim();
  return leftKey.localeCompare(rightKey);
}

function getLatestJapanQuake(rows: JapanQuakeRow[]) {
  return rows.reduce<JapanQuakeRow | null>((latest, row) => {
    if (!latest) return row;
    return compareQuakeTimeline(row.date, row.time, latest.date, latest.time) > 0 ? row : latest;
  }, null);
}

function getLatestGlobalQuake(rows: GlobalQuakeRow[]) {
  return rows.reduce<GlobalQuakeRow | null>((latest, row) => {
    if (!latest) return row;
    return compareQuakeTimeline(row.date, row.time, latest.date, latest.time) > 0 ? row : latest;
  }, null);
}

function getJapanSummary(row: JapanQuakeRow | null): QuakeSummary | null {
  if (!row) return null;

  return {
    date: row.date ?? "-",
    time: row.time ?? "-",
    location: row.location ?? row.epicenter ?? "-",
    magnitude:
      row.magnitude === null || row.magnitude === undefined
        ? "-"
        : String(row.magnitude),
    intensity: row.intensity ?? undefined,
  };
}

function getGlobalSummary(row: GlobalQuakeRow | null): QuakeSummary | null {
  if (!row) return null;

  return {
    date: row.date ?? "-",
    time: row.time ?? "-",
    location: row.location ?? row.title ?? "-",
    magnitude:
      row.magnitude === null || row.magnitude === undefined
        ? "-"
        : String(row.magnitude),
    title: row.title ?? undefined,
    tsunami: row.tsunami,
  };
}

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const [isNavbarOpen, setIsNavbarOpen] = useState(true);
  const [utcDateTime, setUtcDateTime] = useState("----/--/-- --:--:-- UTC");
  const [japanRows, setJapanRows] = useState<JapanQuakeRow[]>([]);
  const [globalRows, setGlobalRows] = useState<GlobalQuakeRow[]>([]);
  const [isTableLoading, setIsTableLoading] = useState(true);
  const [tableError, setTableError] = useState<string | null>(null);
  const [japanSearch, setJapanSearch] = useState("");
  const [globalSearch, setGlobalSearch] = useState("");
  const [japanFilters, setJapanFilters] = useState<JapanFilterState>({
    date: "",
    magnitude: "",
    intensity: "",
  });
  const [globalFilters, setGlobalFilters] = useState<GlobalFilterState>({
    date: "",
    magnitude: "",
    tsunami: "",
  });
  const [showJapanFilters, setShowJapanFilters] = useState(true);
  const [showGlobalFilters, setShowGlobalFilters] = useState(true);
  const [mapRefreshToken, setMapRefreshToken] = useState(0);

  const loadEarthquakeData = useCallback(async () => {
    setIsTableLoading(true);
    setTableError(null);

    try {
      const [japanResponse, globalResponse] = await Promise.all([
        fetch("/api/snowflake/overall?schema=JP", { cache: "no-store" }),
        fetch("/api/snowflake/overall?schema=GLOBAL", { cache: "no-store" }),
      ]);

      if (!japanResponse.ok) {
        throw new Error(`Japan feed failed: ${japanResponse.status}`);
      }

      if (!globalResponse.ok) {
        throw new Error(`Global feed failed: ${globalResponse.status}`);
      }

      const [japanData, globalData] = (await Promise.all([
        japanResponse.json(),
        globalResponse.json(),
      ])) as [JapanQuakeRow[], GlobalQuakeRow[]];

      setJapanRows(japanData);
      setGlobalRows(globalData);
      setMapRefreshToken((current) => current + 1);
    } catch (error) {
      setTableError(error instanceof Error ? error.message : "Failed to load tables");
    } finally {
      setIsTableLoading(false);
    }
  }, []);

  const refreshEarthquakeData = useCallback(
    async (schema: "JP" | "GLOBAL") => {
      setIsTableLoading(true);
      setTableError(null);

      try {
        const [coordsResponse, overallResponse] = await Promise.all([
          fetch(`/api/snowflake/coords?schema=${schema}`, {
            method: "POST",
            cache: "no-store",
          }),
          fetch(`/api/snowflake/overall?schema=${schema}`, {
            method: "POST",
            cache: "no-store",
          }),
        ]);

        if (!coordsResponse.ok) {
          throw new Error(
            `${schema === "JP" ? "Japan" : "Global"} coordinate refresh failed: ${coordsResponse.status}`,
          );
        }

        if (!overallResponse.ok) {
          throw new Error(
            `${schema === "JP" ? "Japan" : "Global"} table refresh failed: ${overallResponse.status}`,
          );
        }

        await loadEarthquakeData();
      } catch (error) {
        setTableError(
          error instanceof Error ? error.message : "Failed to refresh earthquake tables",
        );
      } finally {
        setIsTableLoading(false);
      }
    },
    [loadEarthquakeData],
  );

  useEffect(() => {
    const updateDate = () => {
      const now = new Date();
      const year = now.getUTCFullYear();
      const month = String(now.getUTCMonth() + 1).padStart(2, "0");
      const day = String(now.getUTCDate()).padStart(2, "0");
      const hour = String(now.getUTCHours()).padStart(2, "0");
      const minute = String(now.getUTCMinutes()).padStart(2, "0");
      const second = String(now.getUTCSeconds()).padStart(2, "0");
      setUtcDateTime(`${year}-${month}-${day} ${hour}:${minute}:${second} UTC`);
    };

    updateDate();
    const intervalId = window.setInterval(updateDate, 1000);
    return () => window.clearInterval(intervalId);
  }, []);

  useEffect(() => {
    const frameId = window.requestAnimationFrame(() => {
      void loadEarthquakeData();
    });

    return () => window.cancelAnimationFrame(frameId);
  }, [loadEarthquakeData]);

  const filteredJapanRows = useMemo(() => {
    const searchTerm = normalizeQueryValue(japanSearch);
    const targetMagnitude = Number.parseFloat(japanFilters.magnitude);
    const targetIntensity = normalizeIntensityValue(japanFilters.intensity);

    return japanRows.filter((row) => {
      const rowSearch = normalizeQueryValue(
        [row.date, row.time, row.location, row.epicenter, row.magnitude, row.intensity].join(" "),
      );

      if (searchTerm && !rowSearch.includes(searchTerm)) {
        return false;
      }

      if (japanFilters.date && !(row.date ?? "").startsWith(japanFilters.date)) {
        return false;
      }

      if (japanFilters.magnitude) {
        const rowMagnitude = Number.parseFloat(String(row.magnitude ?? ""));
        if (Number.isNaN(rowMagnitude) || rowMagnitude < targetMagnitude) {
          return false;
        }
      }

      if (targetIntensity && normalizeIntensityValue(row.intensity) !== targetIntensity) {
        return false;
      }

      return true;
    });
  }, [japanFilters.date, japanFilters.intensity, japanFilters.magnitude, japanRows, japanSearch]);

  const filteredGlobalRows = useMemo(() => {
    const searchTerm = normalizeQueryValue(globalSearch);
    const targetMagnitude = Number.parseFloat(globalFilters.magnitude);
    const targetTsunami = globalFilters.tsunami;

    return globalRows.filter((row) => {
      const rowSearch = normalizeQueryValue(
        [row.date, row.time, row.magnitude, row.location, row.title, formatTsunamiValue(row.tsunami)].join(
          " ",
        ),
      );

      if (searchTerm && !rowSearch.includes(searchTerm)) {
        return false;
      }

      if (globalFilters.date && !(row.date ?? "").startsWith(globalFilters.date)) {
        return false;
      }

      if (globalFilters.magnitude) {
        const rowMagnitude = Number.parseFloat(String(row.magnitude ?? ""));
        if (Number.isNaN(rowMagnitude) || rowMagnitude < targetMagnitude) {
          return false;
        }
      }

      if (targetTsunami && normalizeTsunamiValue(row.tsunami) !== targetTsunami) {
        return false;
      }

      return true;
    });
  }, [globalFilters.date, globalFilters.magnitude, globalFilters.tsunami, globalRows, globalSearch]);

  const latestJapanSummary = useMemo(
    () => getJapanSummary(getLatestJapanQuake(japanRows)),
    [japanRows],
  );
  const latestGlobalSummary = useMemo(
    () => getGlobalSummary(getLatestGlobalQuake(globalRows)),
    [globalRows],
  );

  const japanRecordedCount = japanRows.length;
  const japanSignificantCount = japanRows.filter((row) => {
    const magnitude = Number.parseFloat(String(row.magnitude ?? ""));
    return Number.isFinite(magnitude) && magnitude >= 4;
  }).length;
  const globalRecordedCount = globalRows.length;
  const globalSignificantCount = globalRows.filter((row) => {
    const magnitude = Number.parseFloat(String(row.magnitude ?? ""));
    return Number.isFinite(magnitude) && magnitude >= 4;
  }).length;

  useCopilotReadable({
    description: "Snowflake-backed earthquake dashboard data currently visible in the app.",
    value: {
      activeTab,
      utcDateTime,
      japanRows: filteredJapanRows,
      globalRows: filteredGlobalRows,
      latestJapanSummary,
      latestGlobalSummary,
    },
  });

  const tabButtonClass = (tab: TabId) =>
    `tablinks glassflow gf_hover ${activeTab === tab ? "active" : ""}`;

  return (
    <div className={`yuubot-app-shell ${isNavbarOpen ? "navbar-open" : "navbar-closed"}`}>
      <CopilotSidebar
        defaultOpen={false}
        Button={BlackChatButton}
        labels={{
          title: "Cortex Intelligence Hub",
          initial:
            "Connected to Snowflake-backed quake tables. Ask for summaries, filters, or refreshes.",
        }}
      />

      <button
        type="button"
        className="navbar-toggle glassflow gf_hover"
        onClick={() => setIsNavbarOpen((current) => !current)}
        aria-expanded={isNavbarOpen}
        aria-controls="navbar"
        aria-label={isNavbarOpen ? "Close navigation menu" : "Open navigation menu"}
      >
        ☰
      </button>

      <nav id="navbar" className={isNavbarOpen ? "navbar-open" : "navbar-closed"}>
        <h1>YuuBot</h1>
        <ul>
          <li className={tabButtonClass("overview")}>
            <button type="button" onClick={() => setActiveTab("overview")}>
              <i className="fa-solid fa-chart-line" aria-hidden="true" />
              Overview
            </button>
          </li>
          <li className={tabButtonClass("japan")}>
            <button type="button" onClick={() => setActiveTab("japan")}>
              <i className="fa-solid fa-torii-gate" aria-hidden="true" />
              Japan
            </button>
          </li>
          <li className={tabButtonClass("global")}>
            <button type="button" onClick={() => setActiveTab("global")}>
              <i className="fa-solid fa-earth-americas" aria-hidden="true" />
              Global
            </button>
          </li>
          <li className={tabButtonClass("map")}>
            <button type="button" onClick={() => setActiveTab("map")}>
              <i className="fa-solid fa-map-location-dot" aria-hidden="true" />
              Map
            </button>
          </li>
          <li className={tabButtonClass("about")}>
            <button type="button" onClick={() => setActiveTab("about")}>
              <i className="fa-solid fa-circle-info" aria-hidden="true" />
              About
            </button>
          </li>
        </ul>
        <button
          type="button"
          className="navbar-close glassflow gf_hover"
          onClick={() => setIsNavbarOpen(false)}
        >
          Close navbar
        </button>
        <p id="datentime">{utcDateTime}</p>
      </nav>

      <main className="yuubot-main">
        <section className={`window ${activeTab === "overview" ? "visible" : "hidden"}`}>
          <h2>Overview</h2>
          <div className="sidebyside_allquakes">
            <div className="mostrecent_japan glassflow">
              <h3>Most Recent Japan Earthquake</h3>
              {latestJapanSummary ? (
                <div className="overview-japan-summary">
                  <div className="overview-japan-summary__text">
                    <p>Date (in JST): {latestJapanSummary.date}</p>
                    <p>Time: {latestJapanSummary.time}</p>
                    <p>Location: {latestJapanSummary.location}</p>
                    <p>Magnitude: {latestJapanSummary.magnitude}</p>
                    <p>Intensity: {latestJapanSummary.intensity ?? "-"}</p>
                  </div>
                  {latestJapanSummary.intensity ? (
                    <div className="overview-intensity">
                      <span className="shindo-intensity__image-shell">
                        <Image
                          className="shindo-intensity__image"
                          src={getShindoImage(latestJapanSummary.intensity) ?? "/shindo-images/tbp1.png"}
                          alt={`Intensity ${latestJapanSummary.intensity}`}
                          width={124}
                          height={124}
                        />
                      </span>
                    </div>
                  ) : null}
                </div>
              ) : (
                <p>No Japan earthquake data available.</p>
              )}
            </div>
            <div className="mostrecent_global glassflow">
              <h3>Most Recent Global Earthquake</h3>
              {latestGlobalSummary ? (
                <>
                  <p>Date (in UTC): {latestGlobalSummary.date}</p>
                  <p>Time: {latestGlobalSummary.time}</p>
                  <p>Location: {latestGlobalSummary.location}</p>
                  <p>Magnitude: {latestGlobalSummary.magnitude}</p>
                  <p>Tsunami: {formatTsunamiValue(latestGlobalSummary.tsunami)}</p>
                </>
              ) : (
                <p>No global earthquake data available.</p>
              )}
            </div>
          </div>
          <div className="earthquake_counts glassflow">
            <div className="jp_quake_counts">
              <h3>Total Japan Earthquakes Recorded</h3>
              <p>{isTableLoading ? "Loading..." : japanRecordedCount}</p>
            </div>
            <div className="jp_quake_sig_counts">
              <h3>Total Significant Japan Earthquakes (M4.0+)</h3>
              <p>{isTableLoading ? "Loading..." : japanSignificantCount}</p>
            </div>
            <div className="global_quake_counts">
              <h3>Total Global Earthquakes Recorded</h3>
              <p>{isTableLoading ? "Loading..." : globalRecordedCount}</p>
            </div>
            <div className="global_quake_sig_counts">
              <h3>Total Significant Global Earthquakes (M4.0+)</h3>
              <p>{isTableLoading ? "Loading..." : globalSignificantCount}</p>
            </div>
          </div>
        </section>

        <section className={`window ${activeTab === "japan" ? "visible" : "hidden"}`}>
          <h2>Recent Japan Earthquakes</h2>
          <div className="filtering_tools">
            <input
              type="text"
              className="glassflow"
              placeholder="Search by date, location, magnitude, or intensity..."
              value={japanSearch}
              onChange={(event) => setJapanSearch(event.target.value)}
            />
            <button
              id="filter_quakes"
              className="glassflow gf_hover filter-toggle-btn"
              type="button"
              onClick={() => setShowJapanFilters((current) => !current)}
              style={{ height: "52px", padding: "0 20px", whiteSpace: "nowrap" }}
              aria-expanded={showJapanFilters}
              aria-controls="japan-filter-panel"
            >
              <i className="fa-solid fa-filter" aria-hidden="true" />
              {showJapanFilters ? "Hide Filters" : "Show Filters"}
            </button>
          </div>
          <div
            id="japan-filter-panel"
            className={`quake-filter-panel glassflow ${showJapanFilters ? "" : "hidden"}`}
          >
            <div className="quake-filter-grid">
              <label>
                Date
                <input
                  type="date"
                  className="glassflow"
                  value={japanFilters.date}
                  onChange={(event) =>
                    setJapanFilters((current) => ({ ...current, date: event.target.value }))
                  }
                />
              </label>
              <label>
                Magnitude
                <input
                  type="number"
                  step="0.1"
                  className="glassflow"
                  value={japanFilters.magnitude}
                  onChange={(event) =>
                    setJapanFilters((current) => ({ ...current, magnitude: event.target.value }))
                  }
                />
              </label>
              <label>
                Intensity
                <input
                  type="text"
                  className="glassflow"
                  value={japanFilters.intensity}
                  onChange={(event) =>
                    setJapanFilters((current) => ({ ...current, intensity: event.target.value }))
                  }
                  placeholder="e.g. 5+"
                />
              </label>
            </div>
            <div className="quake-filter-actions">
              <button
                type="button"
                className="glassflow gf_hover"
                style={{ padding: "10px 16px" }}
                onClick={() => setJapanFilters({ date: "", magnitude: "", intensity: "" })}
              >
                <i className="fa-solid fa-rotate-left" aria-hidden="true" />
                Clear Filters
              </button>
            </div>
          </div>
          <div className="table_fix_head glassflow">
            <table className="earthquake-table" border={1}>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Location</th>
                  <th>Magnitude</th>
                  <th>Intensity</th>
                </tr>
              </thead>
              <tbody>
                {tableError ? (
                  <tr>
                    <td colSpan={5}>{tableError}</td>
                  </tr>
                ) : isTableLoading ? (
                  <tr>
                    <td colSpan={5}>Loading...</td>
                  </tr>
                ) : filteredJapanRows.length > 0 ? (
                  filteredJapanRows.map((row, index) => {
                    const shindoImage = getShindoImage(row.intensity);

                    return (
                      <tr key={`${row.date ?? "jp"}-${row.time ?? index}-${index}`}>
                        <td>{row.date ?? "-"}</td>
                        <td>{row.time ?? "-"}</td>
                        <td>{row.location ?? row.epicenter ?? "-"}</td>
                        <td>{row.magnitude ?? "-"}</td>
                        <td>
                          {shindoImage ? (
                            <span className="shindo-table-image-shell">
                              <Image
                                className="shindo-table-image"
                                src={shindoImage}
                                alt={`Intensity ${row.intensity}`}
                                width={104}
                                height={104}
                              />
                            </span>
                          ) : (
                            row.intensity ?? "-"
                          )}
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={5}>No rows found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="quake-refresh-row">
            <button
              type="button"
              className="glassflow gf_hover"
              style={{ padding: "10px 16px" }}
              onClick={() => void refreshEarthquakeData("JP")}
              disabled={isTableLoading}
            >
              <i className="fa-solid fa-arrows-rotate" aria-hidden="true" />
              Refresh Japan Data
            </button>
          </div>
        </section>

        <section className={`window ${activeTab === "global" ? "visible" : "hidden"}`}>
          <h2>Recent Global Earthquakes</h2>
          <div className="filtering_tools">
            <input
              type="text"
              className="glassflow"
              placeholder="Search by date, location, title, magnitude, or tsunami..."
              value={globalSearch}
              onChange={(event) => setGlobalSearch(event.target.value)}
            />
            <button
              id="filter_quakes_global"
              className="glassflow gf_hover filter-toggle-btn"
              type="button"
              onClick={() => setShowGlobalFilters((current) => !current)}
              style={{ height: "52px", padding: "0 20px", whiteSpace: "nowrap" }}
              aria-expanded={showGlobalFilters}
              aria-controls="global-filter-panel"
            >
              <i className="fa-solid fa-filter" aria-hidden="true" />
              {showGlobalFilters ? "Hide Filters" : "Show Filters"}
            </button>
          </div>
          <div
            id="global-filter-panel"
            className={`quake-filter-panel glassflow ${showGlobalFilters ? "" : "hidden"}`}
          >
            <div className="quake-filter-grid">
              <label>
                Date
                <input
                  type="date"
                  className="glassflow"
                  value={globalFilters.date}
                  onChange={(event) =>
                    setGlobalFilters((current) => ({ ...current, date: event.target.value }))
                  }
                />
              </label>
              <label>
                Magnitude
                <input
                  type="number"
                  step="0.1"
                  className="glassflow"
                  value={globalFilters.magnitude}
                  onChange={(event) =>
                    setGlobalFilters((current) => ({ ...current, magnitude: event.target.value }))
                  }
                />
              </label>
              <label>
                Tsunami
                <select
                  className="glassflow"
                  value={globalFilters.tsunami}
                  onChange={(event) =>
                    setGlobalFilters((current) => ({ ...current, tsunami: event.target.value }))
                  }
                >
                  <option value="">All</option>
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </label>
            </div>
            <div className="quake-filter-actions">
              <button
                type="button"
                className="glassflow gf_hover"
                style={{ padding: "10px 16px" }}
                onClick={() => setGlobalFilters({ date: "", magnitude: "", tsunami: "" })}
              >
                <i className="fa-solid fa-rotate-left" aria-hidden="true" />
                Clear Filters
              </button>
            </div>
          </div>
          <div className="table_fix_head glassflow">
            <table className="earthquake-table-global" border={1}>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Location</th>
                  <th>Magnitude</th>
                  <th>Tsunami</th>
                </tr>
              </thead>
              <tbody>
                {tableError ? (
                  <tr>
                    <td colSpan={5}>{tableError}</td>
                  </tr>
                ) : isTableLoading ? (
                  <tr>
                    <td colSpan={5}>Loading...</td>
                  </tr>
                ) : filteredGlobalRows.length > 0 ? (
                  filteredGlobalRows.map((row, index) => (
                    <tr key={`${row.date ?? "gl"}-${row.time ?? index}-${index}`}>
                      <td>{row.date ?? "-"}</td>
                      <td>{row.time ?? "-"}</td>
                      <td>{row.location ?? row.title ?? "-"}</td>
                      <td>{row.magnitude ?? "-"}</td>
                      <td>{formatTsunamiValue(row.tsunami)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5}>No rows found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="quake-refresh-row">
            <button
              type="button"
              className="glassflow gf_hover"
              style={{ padding: "10px 16px" }}
              onClick={() => void refreshEarthquakeData("GLOBAL")}
              disabled={isTableLoading}
            >
              <i className="fa-solid fa-arrows-rotate" aria-hidden="true" />
              Refresh Global Data
            </button>
          </div>
        </section>

        <section className={`window ${activeTab === "map" ? "visible" : "hidden"}`}>
          <h2>Map</h2>
          {activeTab === "map" ? <QuakeMap key={mapRefreshToken} /> : null}
        </section>

        <section className={`window ${activeTab === "about" ? "visible" : "hidden"}`}>
          <h2>About</h2>
          <p id="about-text">
            YuuBot is a comprehensive earthquake monitoring system for Japan and globally. It consists of two integrated components: a real-time earthquake data visualization web application and an AI-powered chatbot interface. The system continuously tracks, stores, and presents earthquake data from Japan and other parts of the world, making critical seismic information accessible through visual dashboards and natural language interactions. Created by Dino Wun.
          </p>
          <h3>My Socials</h3>
          <div id="my_socials">
            <span className="glassflow gf_hover socialmedia_boxes">
              <a href="https://github.com/dinwun450" id="social_link" aria-label="GitHub">
                <i className="fa-brands fa-github" aria-hidden="true" />
                GitHub
              </a>
            </span>
            <span className="glassflow gf_hover socialmedia_boxes">
              <a href="http://linkedin.com/in/dinowun" id="social_link" aria-label="LinkedIn">
                <i className="fa-brands fa-linkedin" aria-hidden="true" />
                LinkedIn
              </a>
            </span>
            <span className="glassflow gf_hover socialmedia_boxes">
              <a href="https://www.instagram.com/dinwun450/" id="social_link" aria-label="Instagram">
                <i className="fa-brands fa-instagram" aria-hidden="true" />
                Instagram
              </a>
            </span>
            <span className="glassflow gf_hover socialmedia_boxes">
              <a href="https://www.facebook.com/dino.wun.5/" id="social_link" aria-label="Facebook">
                <i className="fa-brands fa-facebook" aria-hidden="true" />
                Facebook
              </a>
            </span>
          </div>
        </section>

      </main>
    </div>
  );
}
