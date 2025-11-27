import './IconButton.css';

export function IconButton({ 
  icon, 
  label, 
  onClick, 
  disabled = false,
  variant = 'primary',
  type = 'button'
}) {
  return (
    <button
      type={type}
      className={`icon-button icon-button-${variant}`}
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
    >
      {icon && <span className="icon-button-icon">{icon}</span>}
      {label && <span className="icon-button-label">{label}</span>}
    </button>
  );
}

