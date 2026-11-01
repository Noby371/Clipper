import { useEffect, useState } from 'react';
import { HackerApiKeyInput } from './HackerApiKeyInput';
import { useLanguage } from '../locales';
import { resilientFetch } from '../utils/api';

interface NineRouterSettingsProps {
  loading?: boolean;
  onError?: (error: string | null) => void;
}

export const NineRouterSettings: React.FC<NineRouterSettingsProps> = ({ loading = false, onError }) => {
  const { t } = useLanguage();
  
  const [nineRouterKey, setNineRouterKey] = useState<string>(
    () => localStorage.getItem('cheat_clip_nine_router_key') || ''
  );
  const [nineRouterEndpoint, setNineRouterEndpoint] = useState<string>(
    () => localStorage.getItem('cheat_clip_nine_router_endpoint') || 'http://localhost:8000/v1'
  );
  const [nineRouterModel, setNineRouterModel] = useState<string>(
    () => localStorage.getItem('cheat_clip_nine_router_model') || 'default-model'
  );
  const [nineRouterModels, setNineRouterModels] = useState<Array<{ id: string; name: string }>>([]);
  const [loadingModels, setLoadingModels] = useState(false);

  useEffect(() => {
    localStorage.setItem('cheat_clip_nine_router_key', nineRouterKey);
  }, [nineRouterKey]);

  useEffect(() => {
    localStorage.setItem('cheat_clip_nine_router_endpoint', nineRouterEndpoint);
  }, [nineRouterEndpoint]);

  useEffect(() => {
    localStorage.setItem('cheat_clip_nine_router_model', nineRouterModel);
  }, [nineRouterModel]);

  useEffect(() => {
    let isCancelled = false;
    const fetchModels = async () => {
      setLoadingModels(true);
      try {
        const cleanKey = nineRouterKey.trim();
        const res = await resilientFetch('/api/nine-router-models', {
          headers: {
            ...(cleanKey ? { 'X-NineRouter-API-Key': cleanKey, 'Authorization': `Bearer ${cleanKey}` } : {}),
            'X-NineRouter-Endpoint': nineRouterEndpoint
          },
          maxRetries: 2,
          retryDelay: 800,
          silent: true
        });
        if (res.ok && !isCancelled) {
          const data = await res.json();
          if (data.models && Array.isArray(data.models) && data.models.length > 0) {
            setNineRouterModels(data.models);
          }
        }
      } catch (err) {
        console.error('Failed to retrieve 9router models:', err);
      } finally {
        if (!isCancelled) setLoadingModels(false);
      }
    };

    fetchModels();
    return () => {
      isCancelled = true;
    };
  }, [nineRouterKey, nineRouterEndpoint]);

  return (
    <>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <label style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
          {t.form.nineRouterEndpointLabel}
        </label>
        <input
          type="text"
          value={nineRouterEndpoint}
          onChange={(e) => setNineRouterEndpoint(e.target.value)}
          placeholder="http://localhost:8000/v1"
          className="form-input"
          disabled={loading}
          style={{
            padding: '0.6rem 1rem',
            fontSize: '0.875rem',
            height: '42px',
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid var(--border-color)',
            borderRadius: 0
          }}
        />
        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
          Base URL endpoint tempat 9router / LLM server lokal Anda berjalan.
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <label style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
          {t.form.nineRouterApiKeyLabel}
        </label>
        <HackerApiKeyInput
          id="nine-router-key-input"
          value={nineRouterKey}
          onChange={(val) => {
            setNineRouterKey(val);
            if (val.trim() && onError) onError(null);
          }}
          disabled={loading}
          placeholder={t.form.apiKeyPlaceholder}
          revealLabel={t.form.revealKey}
          maskLabel={t.form.maskKey}
        />
        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
          Opsional - hanya jika endpoint lokal Anda membutuhkan autentikasi.
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
          <span>{t.form.nineRouterModelLabel}</span>
          {loadingModels && (
            <span style={{ fontSize: '0.72rem', color: 'var(--primary)', animation: 'pulse 1.5s infinite ease-in-out' }}>
              ⏳ {t.form.fetchingModels}
            </span>
          )}
        </label>
        <select
          className="form-input"
          value={nineRouterModel}
          onChange={(e) => setNineRouterModel(e.target.value)}
          disabled={loading || loadingModels}
          style={{
            padding: '0.6rem 1rem',
            fontSize: '0.875rem',
            height: '42px',
            cursor: 'pointer',
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid var(--border-color)',
            borderRadius: 0
          }}
        >
          {nineRouterModels.length > 0 ? (
            nineRouterModels.map((m) => (
              <option key={m.id} value={m.id} style={{ background: '#0a0a0f', color: '#fff' }}>
                {m.name || m.id}
              </option>
            ))
          ) : (
            <option value="default">Default / Custom Model</option>
          )}
        </select>
      </div>
    </>
  );
};

export default NineRouterSettings;
