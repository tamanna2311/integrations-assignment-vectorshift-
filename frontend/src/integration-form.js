import { useState } from 'react';
import { AirtableIntegration } from './integrations/airtable';
import { NotionIntegration } from './integrations/notion';
import { HubSpotIntegration } from './integrations/hubspot';
import { DataForm } from './data-form';

const integrationMapping = {
    'Notion': NotionIntegration,
    'Airtable': AirtableIntegration,
    'HubSpot': HubSpotIntegration,
};

export const IntegrationForm = () => {
    const [integrationParams, setIntegrationParams] = useState({});
    const [user, setUser] = useState('TestUser');
    const [org, setOrg] = useState('TestOrg');
    const [currType, setCurrType] = useState(null);
    const CurrIntegration = integrationMapping[currType];

    return (
        <div style={{ width: '100%' }}>
            <div style={{ marginBottom: '24px' }}>
                <label className="custom-label">User</label>
                <input
                    className="custom-input"
                    value={user}
                    onChange={(e) => setUser(e.target.value)}
                    placeholder="Enter user ID"
                />
            </div>

            <div style={{ marginBottom: '24px' }}>
                <label className="custom-label">Organization</label>
                <input
                    className="custom-input"
                    value={org}
                    onChange={(e) => setOrg(e.target.value)}
                    placeholder="Enter organization ID"
                />
            </div>

            <div style={{ marginBottom: '24px' }}>
                <label className="custom-label">Select Integration</label>
                <div className="integration-grid">
                    {Object.keys(integrationMapping).map((type) => (
                        <div
                            key={type}
                            className={`integration-option ${currType === type ? 'selected' : ''}`}
                            onClick={() => setCurrType(type)}
                        >
                            <div className="integration-icon">
                                {type === 'Notion' ? '📝' : type === 'Airtable' ? '📊' : '🚀'}
                            </div>
                            <div style={{ fontWeight: 600 }}>{type}</div>
                        </div>
                    ))}
                </div>
            </div>

            {currType &&
                <div style={{ marginTop: '32px', borderTop: '1px solid var(--border-color)', paddingTop: '24px' }}>
                    <CurrIntegration user={user} org={org} integrationParams={integrationParams} setIntegrationParams={setIntegrationParams} />
                </div>
            }

            {integrationParams?.credentials &&
                <div style={{ marginTop: '32px' }}>
                    <DataForm integrationType={integrationParams?.type} credentials={integrationParams?.credentials} />
                </div>
            }
        </div>
    );
}
