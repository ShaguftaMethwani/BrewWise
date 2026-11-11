import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Home } from './pages/Home';
import { ProfileEdit } from './pages/ProfileEdit';
import { RecipeView } from './pages/RecipeView';
import { BrewHistory } from './pages/BrewHistory';
import { Settings } from './pages/Settings';

function App() {
  return (
    <BrowserRouter>
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Navbar />
        <main style={{ flex: 1 }}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/profile/:id" element={<ProfileEdit />} />
            <Route path="/recipe/:id" element={<RecipeView />} />
            <Route path="/history" element={<BrewHistory />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
