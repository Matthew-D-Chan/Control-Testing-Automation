import cibcLogoLetters from '../../assets/cibc_logo_letters.svg';
export function Header({ onNavigateHome }) {
  return (
    <header className="app-header">
      <div className="header-content">
        <div className="header-logo">
          <button 
            onClick={onNavigateHome}
            className="logo-button"
            aria-label="Go to home"
          >
            <img src={cibcLogoLetters} alt="CIBC Logo" className="logo-img" />
          </button>
        </div>
      </div>
    </header>
  );
}

