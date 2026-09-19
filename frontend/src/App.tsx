import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell, FocusShell } from "./components/AppShell";
import { Home } from "./pages/Home";
import { Welcome } from "./pages/Welcome";
import { Onboarding } from "./pages/Onboarding";
import { Login } from "./pages/Login";
import { PracticeSelect } from "./pages/PracticeSelect";
import { PracticeAnalysis } from "./pages/PracticeAnalysis";
import { MicTest } from "./pages/MicTest";
import { Learn } from "./pages/Learn";
import { ISpyPhase1 } from "./pages/ISpyPhase1";
import { ISpyPhase2 } from "./pages/ISpyPhase2";
import { SessionSummary } from "./pages/SessionSummary";
import { Progress } from "./pages/Progress";
import { Vocabulary } from "./pages/Vocabulary";
import { Journal } from "./pages/Journal";
import { JournalEntryPage } from "./pages/JournalEntryPage";
import { JournalNew } from "./pages/JournalNew";
import { Profile } from "./pages/Profile";
import { SceneRoute } from "./components/SceneRoute";
import { SessionRoute } from "./components/SessionRoute";

export default function App() {
  return (
    <Routes>
      <Route element={<FocusShell />}>
        <Route path="/" element={<Welcome />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="/login" element={<Login />} />
        <Route path="/practice/sessions/:sessionId" element={<SessionRoute />}>
          <Route path="analysis" element={<PracticeAnalysis />} />
          <Route path="mic-test" element={<MicTest />} />
          <Route path="learn" element={<Learn />} />
          <Route path="ispy-1" element={<ISpyPhase1 />} />
          <Route path="ispy-2" element={<ISpyPhase2 />} />
          <Route path="summary" element={<SessionSummary />} />
        </Route>
        <Route path="/practice/:sceneId/*" element={<SceneRoute />} />
      </Route>
      <Route element={<AppShell />}>
        <Route path="/home" element={<Home />} />
        <Route path="/practice" element={<PracticeSelect />} />
        <Route path="/progress" element={<Progress />} />
        <Route path="/vocabulary" element={<Vocabulary />} />
        <Route path="/journal" element={<Journal />} />
        <Route path="/journal/new" element={<JournalNew />} />
        <Route path="/journal/:entryId" element={<JournalEntryPage />} />
        <Route path="/profile" element={<Profile />} />
      </Route>
      <Route path="*" element={<Navigate to="/home" replace />} />
    </Routes>
  );
}
