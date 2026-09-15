import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, ProgressTrail, Tabs } from "../components/ui";
import { ArrowRightIcon, PlayIcon } from "../components/icons";
import { SceneArt } from "../components/SceneArt";
import { getScene, leaderboard, scenarioProgress } from "../data/mock";
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
  const { xp, vocabulary } = useAppState();
  const [filter, setFilter] = useState<Filter>("all");

  const rows = scenarioProgress.filter((item) => filter === "all" || item.status === filter);
  const board = leaderboard
    .map((row) => (row.isYou ? { ...row, xp } : row))
    .sort((a, b) => b.xp - a.xp)
    .map((row, index) => ({ ...row, rank: index + 1 }));
  const active = scenarioProgress.find((item) => item.status === "in-progress");
  const activeScene = active ? getScene(active.sceneId) : null;

  return (
    <div className="stack">
      <h1>Progress</h1>
      <p className="muted">Where you are, what you found, and what comes next.</p>

      {activeScene && active ? (
        <Card lifted>
          <div className="stack-2">
            <span className="label muted">I-Spy in progress</span>
            <div className="row">
              <span className="thumb">
                <SceneArt scene={activeScene.art} />
              </span>
              <div className="grow stack-2">
                <strong>{activeScene.title}</strong>
                <span className="small muted">{activeScene.blurb}</span>
                <ProgressTrail
                  value={active.spokenItems}
                  total={active.totalItems}
                  label={`${active.spokenItems} / ${active.totalItems} items spoken`}
                />
              </div>
            </div>
            <Button onClick={() => navigate(`/practice/${activeScene.id}/learn`)}>
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
        <Tabs options={filters} value={filter} onChange={setFilter} />
        <div className="stack-2">
          {rows.map((row) => {
            const scene = getScene(row.sceneId);
            return (
              <Card key={row.sceneId} plain>
                <div className="row">
                  <span className="thumb">
                    <SceneArt scene={scene.art} />
                  </span>
                  <div className="grow stack-2">
                    <div className="spread">
                      <strong>{scene.title}</strong>
                      <span className="pill pill--new">{row.level}</span>
                    </div>
                    <ProgressTrail
                      value={row.spokenItems}
                      total={row.totalItems}
                      label={`${row.spokenItems}/${row.totalItems} spoken · ${row.status.replace("-", " ")}`}
                    />
                  </div>
                </div>
                <div style={{ marginTop: "var(--space-3)" }}>
                  <Button
                    variant="secondary"
                    block
                    onClick={() => navigate(`/practice/${scene.id}/learn`)}
                  >
                    {row.status === "in-progress" ? "Continue scenario" : "Replay scene"}
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
