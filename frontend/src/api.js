const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

async function getErrorMessage(response, path) {
  try {
    const payload = await response.json();
    if (typeof payload?.detail === "string" && payload.detail) {
      return payload.detail;
    }
  } catch {
    // Ignore JSON parsing failures and fall back to a generic message.
  }
  return `Request failed for ${path}: ${response.status}`;
}

async function request(path, options) {
  const response = await fetch(`${BASE_URL}${path}`, options);
  if (!response.ok) {
    throw new Error(await getErrorMessage(response, path));
  }
  return response.json();
}

export function getDashboardSummary() {
  return request("/api/dashboard/summary");
}

export function getAIStatus() {
  return request("/api/system/ai-status");
}

export function getAccounts() {
  return request("/api/accounts");
}

export function getCases() {
  return request("/api/cases");
}

export function getCase(caseId) {
  return request(`/api/cases/${caseId}`);
}

export function getPredictions() {
  return request("/api/predictions");
}

export function getPrediction(predictionId) {
  return request(`/api/predictions/${predictionId}`);
}

export function getContractFacts(contractId) {
  return request(`/api/contracts/${contractId}/facts`);
}

export function getContractAIBrief(contractId, focus = "contract") {
  const query = new URLSearchParams({ focus });
  return request(`/api/contracts/${contractId}/ai-brief?${query.toString()}`);
}

export function getDocumentContentUrl(documentId) {
  return `${BASE_URL}/api/documents/${documentId}/content`;
}

export function importContractDocument(contractId, documentType, file) {
  const formData = new FormData();
  formData.append("document_type", documentType);
  formData.append("file", file);

  return request(`/api/contracts/${contractId}/documents/import`, {
    method: "POST",
    body: formData,
  });
}

// ─── Setup API ────────────────────────────────────────────────────────────────

export function setupListAccounts() {
  return request("/api/setup/accounts");
}

export function setupCreateAccount(name) {
  return request("/api/setup/accounts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
}

export function setupDeleteAccount(accountId) {
  return request(`/api/setup/accounts/${accountId}`, { method: "DELETE" });
}

export function setupListContracts(accountId) {
  return request(`/api/setup/accounts/${accountId}/contracts`);
}

export function setupCreateContract(accountId, data) {
  return request(`/api/setup/accounts/${accountId}/contracts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function setupDeleteContract(contractId) {
  return request(`/api/setup/contracts/${contractId}`, { method: "DELETE" });
}

export function setupListInvoices(contractId) {
  return request(`/api/setup/contracts/${contractId}/invoices`);
}

export function setupCreateInvoice(contractId, data) {
  return request(`/api/setup/contracts/${contractId}/invoices`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function setupDeleteInvoice(invoiceId) {
  return request(`/api/setup/invoices/${invoiceId}`, { method: "DELETE" });
}

export function setupReset() {
  return request("/api/setup/reset", { method: "POST" });
}

export function setupShiftRenewal(contractId, daysFromToday) {
  return request(`/api/setup/contracts/${contractId}/shift-renewal`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ days_from_today: daysFromToday }),
  });
}
