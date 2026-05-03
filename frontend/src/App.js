import { IntegrationForm } from './integration-form';
import './index.css';

function App() {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '40px 20px'
    }}>
      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        <h1 className="gradient-text" style={{ fontSize: '3rem', margin: '0 0 10px 0' }}>
          VectorShift
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.2rem', margin: 0 }}>
          The Fastest Way to Build AI Apps and Workflows
        </p>
      </div>

      <div className="glass-card" style={{ width: '100%', maxWidth: '600px' }}>
        <IntegrationForm />
      </div>
    </div>
  );
}

export default App;
