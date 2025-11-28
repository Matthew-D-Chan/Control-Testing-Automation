import { Header } from './Header';
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

