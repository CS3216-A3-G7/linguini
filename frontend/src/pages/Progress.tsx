import { MediaImage } from "../components/MediaImage";
import { LoadingScreen } from "../components/LoadingScreen";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, ProgressTrail, Tabs } from "../components/ui";
import { ArrowRightIcon, PlayIcon } from "../components/icons";
import { SceneCatalogStatus } from "../components/SceneCatalogStatus";
import { useAppState } from "../state/useAppState";

type Filter = "all" | "in-progress" | "completed" | "mastered";

const filters: { id: Filter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "in-progress", label: "In progress" },
  { id: "completed", label: "Completed" },
  { id: "mastered", label: "Mastered" },
];

export function Progress() {
  const navigate = useNavigate();
  const { xp, vocabulary, progress, progressLoading, progressError, vocabularyLoading, vocabularyError, scenes, learner } = useAppState();
  const [filter, setFilter] = useState<Filter>("all");

  if (progressError || vocabularyError) {
    return <div className="stack"><h1>Progress</h1><p role="alert">{progressError || vocabularyError} Reload to retry.</p></div>;
  }
  if (progressLoading || vocabularyLoading || !progress) {
    return <div className="stack"><h1>Progress</h1><LoadingScreen label="Loading progress…" /></div>;
  }
  const scenarioProgress = progress.scenarios;

  const rows = scenarioProgress.filter((item) => filter === "all" || item.status === filter);
  const board = progress.leaderboard
    .map((row) => (row.isYou ? { ...row, xp, name: learner.name } : row))
    .sort((a, b) => b.xp - a.xp)
    .map((row, index) => ({ ...row, rank: index + 1 }));
  const active = scenarioProgress.find((item) => item.status === "in-progress");
  const activeScene = scenes.find((scene) => scene.id === active?.sceneId);

  return (
    <div className="stack">
      <h1>Progress</h1>
      <p className="small muted">Introductions and evaluated answers add vocabulary credit.</p>

      {active ? (
        <Card lifted>
          <div className="stack-2">
            <span className="label muted">I-Spy in progress</span>
            <div className="row">
              <span className="thumb">
                <MediaImage assetId={active.mediaAssetId} title={active.title} imageUrl={activeScene?.imageUrl} />
              </span>
              <div className="grow stack-2">
                <strong>{active.title}</strong>
                <span className="small muted">{activeScene?.blurb}</span>
                <ProgressTrail
                  value={active.completedTaskCount}
                  total={active.totalTaskCount}
                  label={`${active.completedTaskCount} / ${active.totalTaskCount} tasks completed`}
                />
              </div>
            </div>
            <Button onClick={() => navigate(`/practice/sessions/${active.sessionId}/learn`)}>
              <PlayIcon size={16} /> Resume scenario
            </Button>
          </div>
        </Card>
      ) : null}

      <div className="stat-grid">
        <div className="stat">
          <div className="stat__value">{xp}</div>
          <span className="small muted">Total XP</span>
        </div>
        <div className="stat">
          <div className="stat__value">{vocabulary.length}</div>
          <span className="small muted">Words saved</span>
        </div>
        <div className="stat">
          <div className="stat__value">{scenarioProgress.length}</div>
          <span className="small muted">Scenarios</span>
        </div>
      </div>

      <Button variant="secondary" block onClick={() => navigate("/vocabulary")}>
        My vocabulary <ArrowRightIcon />
      </Button>

      <div className="stack-2">
        <h2>Scenarios</h2>
        <SceneCatalogStatus />
        <Tabs options={filters} value={filter} onChange={setFilter} />
        <div className="stack-2">
          {rows.map((row) => {
            const scene = scenes.find((candidate) => candidate.id === row.sceneId);
            return (
              <Card key={row.sceneId} plain>
                <div className="row">
                  <span className="thumb">
                    <MediaImage assetId={row.mediaAssetId} title={row.title} imageUrl={scene?.imageUrl} />
                  </span>
                  <div className="grow stack-2">
                    <div className="spread">
                      <strong>{row.title}</strong>
                      <span className="pill pill--new">{row.level}</span>
                    </div>
                    <ProgressTrail
                      value={row.completedTaskCount}
                      total={row.totalTaskCount}
                      label={`${row.completedTaskCount}/${row.totalTaskCount} completed · ${row.status.replace("-", " ")}`}
                    />
                  </div>
                </div>
                <div style={{ marginTop: "var(--space-3)" }}>
                  <Button
                    variant="secondary"
                    block
                    onClick={() => navigate(`/practice/sessions/${row.sessionId}/${row.status === "in-progress" ? "learn" : "summary"}`)}
                  >
                    {row.status === "in-progress" ? "Continue scenario" : "View summary"}
                  </Button>
                </div>
              </Card>
            );
          })}
          {rows.length === 0 ? <p className="small muted">Nothing here yet — start a scene.</p> : null}
        </div>
      </div>

      <div className="stack-2">
        <h2>Leaderboard</h2>
        <Card>
          <div className="list">
            {board.length === 0 ? <p className="small muted">No leaderboard for this language yet.</p> : null}
            {board.map((row) => (
              <div key={row.rank} className="list__row" style={{ cursor: "default" }}>
                <span className="chip__marker">{row.rank}</span>
                <span className="grow">
                  <strong>{row.name}</strong>
                  {row.isYou ? <span className="small muted"> · you</span> : null}
                </span>
                <span className="pill pill--xp">{row.xp} XP</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
