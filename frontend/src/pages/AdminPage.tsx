import { useEffect, useState } from "react";
import {
  backupDatabase,
  deactivateIntegrationSetting,
  downloadCustomsTariffExcel,
  downloadIntegrationFile,
  downloadTransportTariffExcel,
  getAuditLogs,
  getBackups,
  getIntegrationLogs,
  getIntegrationSettings,
  getApprovalIntegrationPayload,
  getSystemStatus,
  saveIntegrationSetting,
  updateIntegrationSetting,
  type AuditLogItem,
  type BackupFileItem,
  type IntegrationLogItem,
  type IntegrationSetting,
  type IntegrationSettingPayload,
  type SystemStatus,
  exportApprovalIntegration,
} from "../api/client";
import { getErrorMessage } from "../error";
import { saveBlob, todayStamp } from "../download";

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function defaultIntegrationForm(): IntegrationSettingPayload {
  return {
    integration_name: "ERP",
    integration_type: "FILE_EXPORT",
    endpoint_url: null,
    export_format: "JSON",
    is_active: true,
    description: "",
  };
}

export function AdminPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [backups, setBackups] = useState<BackupFileItem[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [integrationSettings, setIntegrationSettings] = useState<IntegrationSetting[]>([]);
  const [integrationLogs, setIntegrationLogs] = useState<IntegrationLogItem[]>([]);
  const [integrationForm, setIntegrationForm] = useState<IntegrationSettingPayload>(
    defaultIntegrationForm(),
  );
  const [editingIntegrationId, setEditingIntegrationId] = useState<number | null>(null);
  const [integrationApprovalId, setIntegrationApprovalId] = useState("");
  const [integrationPayloadPreview, setIntegrationPayloadPreview] = useState("");
  const [filters, setFilters] = useState({
    user_name: "",
    action: "",
    entity_type: "",
    start_date: "",
    end_date: "",
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadAll() {
    try {
      setLoading(true);
      setError("");
      const [statusData, backupRows, auditRows, integrationSettingRows, integrationLogRows] = await Promise.all([
        getSystemStatus(),
        getBackups(),
        getAuditLogs(),
        getIntegrationSettings(),
        getIntegrationLogs(),
      ]);
      setStatus(statusData);
      setBackups(backupRows);
      setAuditLogs(auditRows);
      setIntegrationSettings(integrationSettingRows);
      setIntegrationLogs(integrationLogRows);
    } catch (error) {
      setError(getErrorMessage(error, "Admin data load failed"));
    } finally {
      setLoading(false);
    }
  }

  async function runBackup() {
    try {
      setLoading(true);
      setError("");
      const result = await backupDatabase();
      setMessage(
        result.status === "manual_required"
          ? result.message ?? "PostgreSQL backup requires pg_dump."
          : `Backup complete: ${result.backup_file}`,
      );
      setBackups(await getBackups());
      setAuditLogs(await getAuditLogs());
    } catch (error) {
      const responseStatus = (error as { response?: { status?: number } }).response?.status;
      const message = responseStatus === 403 ? "권한이 없습니다." : getErrorMessage(error, "DB backup failed");
      setError(message);
      alert(message);
    } finally {
      setLoading(false);
    }
  }

  async function searchAuditLogs() {
    try {
      setLoading(true);
      setError("");
      setAuditLogs(
        await getAuditLogs({
          user_name: filters.user_name || undefined,
          action: filters.action || undefined,
          entity_type: filters.entity_type || undefined,
          start_date: filters.start_date || undefined,
          end_date: filters.end_date || undefined,
        }),
      );
    } catch (error) {
      setError(getErrorMessage(error, "Audit log search failed"));
    } finally {
      setLoading(false);
    }
  }

  async function downloadTransportTariffs() {
    try {
      setLoading(true);
      setError("");
      const blob = await downloadTransportTariffExcel();
      saveBlob(blob, `transport_tariff_${todayStamp()}.xlsx`);
      setAuditLogs(await getAuditLogs());
    } catch (error) {
      const message = getErrorMessage(error, "운송 Tariff Excel 다운로드 실패");
      setError(message);
      alert(message);
    } finally {
      setLoading(false);
    }
  }

  async function downloadCustomsTariffs() {
    try {
      setLoading(true);
      setError("");
      const blob = await downloadCustomsTariffExcel();
      saveBlob(blob, `customs_tariff_${todayStamp()}.xlsx`);
      setAuditLogs(await getAuditLogs());
    } catch (error) {
      const message = getErrorMessage(error, "통관 Tariff Excel 다운로드 실패");
      setError(message);
      alert(message);
    } finally {
      setLoading(false);
    }
  }

  function editIntegrationSetting(setting: IntegrationSetting) {
    setEditingIntegrationId(setting.id);
    setIntegrationForm({
      integration_name: setting.integration_name,
      integration_type: setting.integration_type,
      endpoint_url: setting.endpoint_url,
      export_format: setting.export_format,
      is_active: setting.is_active,
      description: setting.description,
    });
  }

  function resetIntegrationForm() {
    setEditingIntegrationId(null);
    setIntegrationForm(defaultIntegrationForm());
  }

  async function submitIntegrationSetting() {
    try {
      setLoading(true);
      setError("");
      if (editingIntegrationId) {
        await updateIntegrationSetting(editingIntegrationId, integrationForm);
      } else {
        await saveIntegrationSetting(integrationForm);
      }
      setIntegrationSettings(await getIntegrationSettings());
      setAuditLogs(await getAuditLogs());
      resetIntegrationForm();
      setMessage("Integration setting saved.");
    } catch (error) {
      const message = getErrorMessage(error, "Integration setting save failed");
      setError(message);
      alert(message);
    } finally {
      setLoading(false);
    }
  }

  async function deactivateIntegration(id: number) {
    try {
      setLoading(true);
      setError("");
      await deactivateIntegrationSetting(id);
      setIntegrationSettings(await getIntegrationSettings());
      setAuditLogs(await getAuditLogs());
    } catch (error) {
      const message = getErrorMessage(error, "Integration setting deactivate failed");
      setError(message);
      alert(message);
    } finally {
      setLoading(false);
    }
  }

  async function previewApprovalPayload() {
    if (!integrationApprovalId) return;
    try {
      setLoading(true);
      setError("");
      const payload = await getApprovalIntegrationPayload(Number(integrationApprovalId));
      setIntegrationPayloadPreview(JSON.stringify(payload, null, 2));
    } catch (error) {
      const message = getErrorMessage(error, "Approval payload preview failed");
      setError(message);
      alert(message);
    } finally {
      setLoading(false);
    }
  }

  async function exportApprovalPayload() {
    if (!integrationApprovalId) return;
    try {
      setLoading(true);
      setError("");
      const result = await exportApprovalIntegration(Number(integrationApprovalId), {
        integration_name: integrationForm.integration_name || "ERP",
        export_format: integrationForm.export_format,
      });
      if (result.download_url) {
        const blob = await downloadIntegrationFile(result.download_url);
        saveBlob(blob, result.file_name ?? `approval_${integrationApprovalId}.json`);
      }
      setIntegrationLogs(await getIntegrationLogs());
      setAuditLogs(await getAuditLogs());
      setMessage(`Integration export ${result.status}`);
    } catch (error) {
      const message = getErrorMessage(error, "Approval JSON export failed");
      setError(message);
      alert(message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  return (
    <div className="stack">
      {error && <div className="error-box">{error}</div>}
      {loading && <div className="loading">처리 중...</div>}

      <section className="panel">
        <div className="section-heading">
          <h2>Admin Operations</h2>
          <div className="toolbar">
            <button type="button" onClick={loadAll}>
              Refresh
            </button>
            <button type="button" onClick={runBackup}>
              DB Backup
            </button>
          </div>
        </div>
        <div className="meta-line">{message}</div>
      </section>

      {status && (
        <section className="panel">
          <h2>System Status</h2>
          <div className="stat-grid">
            <div className="stat-card"><span>Database</span><strong>{status.database}</strong></div>
            <div className="stat-card"><span>DB Type</span><strong>{status.database_type}</strong></div>
            <div className="stat-card"><span>APP ENV</span><strong>{status.app_env}</strong></div>
            <div className="stat-card"><span>Uploads</span><strong>{status.upload_folder_exists ? "ok" : "missing"}</strong></div>
            <div className="stat-card"><span>PDF Reports</span><strong>{status.generated_reports_folder_exists ? "ok" : "missing"}</strong></div>
            <div className="stat-card"><span>Logs</span><strong>{status.logs_folder_exists ? "ok" : "missing"}</strong></div>
            <div className="stat-card"><span>Backups</span><strong>{status.backup_folder_exists ? "ok" : "missing"}</strong></div>
            <div className="stat-card"><span>Approvals</span><strong>{status.approval_case_count}</strong></div>
            <div className="stat-card"><span>Workflows</span><strong>{status.workflow_count}</strong></div>
            <div className="stat-card"><span>Quotes</span><strong>{status.quote_count}</strong></div>
            <div className="stat-card"><span>PDF Files</span><strong>{status.report_file_count}</strong></div>
          </div>
          <div className="meta-line">Database URL: {status.database_url_masked}</div>
        </section>
      )}

      <section className="panel">
        <div className="section-heading">
          <h2>Tariff Excel Export</h2>
          <div className="toolbar">
            <button type="button" onClick={downloadTransportTariffs}>
              운송 Tariff Excel
            </button>
            <button type="button" onClick={downloadCustomsTariffs}>
              통관 Tariff Excel
            </button>
          </div>
        </div>
        <div className="meta-line">
          결재를 통해 축적된 운송/통관 Tariff DB를 Excel로 다운로드합니다.
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <h2>Integrations</h2>
          <div className="toolbar">
            <button type="button" onClick={submitIntegrationSetting}>
              {editingIntegrationId ? "Update Setting" : "Add Setting"}
            </button>
            <button type="button" className="secondary-button" onClick={resetIntegrationForm}>
              Reset
            </button>
          </div>
        </div>
        <div className="form-grid compact">
          <label className="field">
            <span>Name</span>
            <input
              value={integrationForm.integration_name}
              onChange={(event) =>
                setIntegrationForm((current) => ({
                  ...current,
                  integration_name: event.target.value,
                }))
              }
            />
          </label>
          <label className="field">
            <span>Type</span>
            <select
              value={integrationForm.integration_type}
              onChange={(event) =>
                setIntegrationForm((current) => ({
                  ...current,
                  integration_type: event.target.value as IntegrationSettingPayload["integration_type"],
                }))
              }
            >
              <option value="FILE_EXPORT">FILE_EXPORT</option>
              <option value="API">API</option>
              <option value="WEBHOOK">WEBHOOK</option>
            </select>
          </label>
          <label className="field">
            <span>Format</span>
            <select
              value={integrationForm.export_format}
              onChange={(event) =>
                setIntegrationForm((current) => ({
                  ...current,
                  export_format: event.target.value as IntegrationSettingPayload["export_format"],
                }))
              }
            >
              <option value="JSON">JSON</option>
              <option value="CSV">CSV</option>
              <option value="EXCEL">EXCEL</option>
            </select>
          </label>
          <label className="field">
            <span>Endpoint URL</span>
            <input
              value={integrationForm.endpoint_url ?? ""}
              onChange={(event) =>
                setIntegrationForm((current) => ({
                  ...current,
                  endpoint_url: event.target.value || null,
                }))
              }
            />
          </label>
          <label className="field">
            <span>Description</span>
            <input
              value={integrationForm.description ?? ""}
              onChange={(event) =>
                setIntegrationForm((current) => ({
                  ...current,
                  description: event.target.value || null,
                }))
              }
            />
          </label>
          <label className="check-field">
            <input
              type="checkbox"
              checked={integrationForm.is_active}
              onChange={(event) =>
                setIntegrationForm((current) => ({
                  ...current,
                  is_active: event.target.checked,
                }))
              }
            />
            <span>Active</span>
          </label>
        </div>

        <div className="toolbar form-actions">
          <input
            placeholder="Approval Case ID"
            value={integrationApprovalId}
            onChange={(event) => setIntegrationApprovalId(event.target.value)}
          />
          <button type="button" onClick={previewApprovalPayload}>
            Approval Payload 보기
          </button>
          <button type="button" onClick={exportApprovalPayload}>
            Approval JSON Export
          </button>
        </div>
        {integrationPayloadPreview && (
          <pre className="report-preview">{integrationPayloadPreview}</pre>
        )}

        <h3>Integration Settings</h3>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Type</th>
                <th>Format</th>
                <th>Endpoint</th>
                <th>Active</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {integrationSettings.map((setting) => (
                <tr key={setting.id}>
                  <td>{setting.id}</td>
                  <td>{setting.integration_name}</td>
                  <td>{setting.integration_type}</td>
                  <td>{setting.export_format}</td>
                  <td>{setting.endpoint_url ?? "-"}</td>
                  <td>{setting.is_active ? "Y" : "N"}</td>
                  <td>
                    <button type="button" onClick={() => editIntegrationSetting(setting)}>
                      Edit
                    </button>
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => deactivateIntegration(setting.id)}
                    >
                      Disable
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h3>Integration Logs</h3>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Entity</th>
                <th>Entity ID</th>
                <th>Status</th>
                <th>Created By</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {integrationLogs.map((log) => (
                <tr key={log.id}>
                  <td>{log.id}</td>
                  <td>{log.integration_name}</td>
                  <td>{log.entity_type}</td>
                  <td>{log.entity_id}</td>
                  <td>{log.status}</td>
                  <td>{log.created_by ?? "-"}</td>
                  <td>{log.created_at.slice(0, 19).replace("T", " ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h2>DB Backups</h2>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>File</th>
                <th className="number">Size</th>
                <th>Created</th>
                <th>Path</th>
              </tr>
            </thead>
            <tbody>
              {backups.map((backup) => (
                <tr key={backup.file_name}>
                  <td>{backup.file_name}</td>
                  <td className="number">{formatBytes(backup.file_size)}</td>
                  <td>{backup.created_at.slice(0, 19).replace("T", " ")}</td>
                  <td>{backup.file_path}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <h2>Audit Logs</h2>
          <button type="button" onClick={searchAuditLogs}>
            Search
          </button>
        </div>
        <div className="form-grid compact">
          <label className="field">
            <span>User</span>
            <input
              value={filters.user_name}
              onChange={(event) => setFilters((current) => ({ ...current, user_name: event.target.value }))}
            />
          </label>
          <label className="field">
            <span>Action</span>
            <input
              value={filters.action}
              onChange={(event) => setFilters((current) => ({ ...current, action: event.target.value }))}
            />
          </label>
          <label className="field">
            <span>Entity</span>
            <input
              value={filters.entity_type}
              onChange={(event) => setFilters((current) => ({ ...current, entity_type: event.target.value }))}
            />
          </label>
          <label className="field">
            <span>Start Date</span>
            <input
              type="date"
              value={filters.start_date}
              onChange={(event) => setFilters((current) => ({ ...current, start_date: event.target.value }))}
            />
          </label>
          <label className="field">
            <span>End Date</span>
            <input
              type="date"
              value={filters.end_date}
              onChange={(event) => setFilters((current) => ({ ...current, end_date: event.target.value }))}
            />
          </label>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>User</th>
                <th>Action</th>
                <th>Entity</th>
                <th>Entity ID</th>
                <th>Detail</th>
                <th>IP</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.map((log) => (
                <tr key={log.id}>
                  <td>{log.id}</td>
                  <td>{log.user_name ?? "-"}</td>
                  <td>{log.action}</td>
                  <td>{log.entity_type}</td>
                  <td>{log.entity_id ?? "-"}</td>
                  <td>{log.detail ?? "-"}</td>
                  <td>{log.ip_address ?? "-"}</td>
                  <td>{log.created_at.slice(0, 19).replace("T", " ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
