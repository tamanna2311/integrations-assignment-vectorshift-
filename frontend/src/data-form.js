import { useState } from 'react';
import axios from 'axios';

const endpointMapping = {
    'Notion': 'notion',
    'Airtable': 'airtable',
    'HubSpot': 'hubspot',
};

export const DataForm = ({ integrationType, credentials }) => {
    const [loadedData, setLoadedData] = useState(null);
    const endpoint = endpointMapping[integrationType];

    const handleLoad = async () => {
        try {
            const formData = new FormData();
            formData.append('credentials', JSON.stringify(credentials));
            const response = await axios.post(`http://localhost:8000/integrations/${endpoint}/load`, formData);
            const data = response.data;
            setLoadedData(data);
        } catch (e) {
            alert(e?.response?.data?.detail);
        }
    }

    return (
        <div style={{ width: '100%' }}>
            <div style={{ marginBottom: '16px' }}>
                <label className="custom-label">Loaded Data</label>
                <div className="data-display">
                    {loadedData ? JSON.stringify(loadedData, null, 2) : 'No data loaded yet. Click "Load Data" to fetch.'}
                </div>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
                <button
                    onClick={handleLoad}
                    className="gradient-button"
                    style={{ flex: 1 }}
                >
                    Load Data
                </button>
                <button
                    onClick={() => setLoadedData(null)}
                    className="gradient-button"
                    style={{ flex: 1, background: 'rgba(255, 255, 255, 0.1)', boxShadow: 'none' }}
                >
                    Clear Data
                </button>
            </div>
        </div>
    );
}
