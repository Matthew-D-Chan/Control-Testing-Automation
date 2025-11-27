import { Header } from './Header';
import './AppLayout.css';

export function AppLayout({ children, onNavigateHome }) {
  return (
    <div className="app-layout">
      <Header onNavigateHome={onNavigateHome} />
      <main className="app-main">
        {children}
      </main>
    </div>
  );
}

