let pendingThreadId = null;
let collectionCache = [];

const SUCCESSFUL_CONFIRMATION_STATUSES = new Set([
    "saved",
    "deleted",
    "updated",
]);


// Converte un valore in testo HTML sicuro per l'inserimento nel DOM.
function escapeHtml(value) {
    if (value === null || value === undefined) {
        return "-";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


// Restituisce le classi CSS associate alla condizione di una sneaker.
function conditionBadgeClass(condition) {
    switch (condition) {
        case "new":
            return "bg-green-lt text-green";
        case "like_new":
            return "bg-blue-lt text-blue";
        case "used":
            return "bg-yellow-lt text-yellow";
        case "worn":
            return "bg-red-lt text-red";
        default:
            return "";
    }
}


// Traduce il valore interno della condizione nella relativa etichetta italiana.
function conditionLabel(condition) {
    const labels = {
        new: "Nuova",
        like_new: "Come nuova",
        used: "Usata",
        worn: "Consumata",
    };

    return labels[condition] ?? condition;
}


// Traduce il nome tecnico di un campo nella relativa etichetta per la UI.
function formatFieldName(field) {
    const labels = {
        brand: "Brand",
        model: "Modello",
        colorway: "Colorway",
        style_code: "Style code",
        size: "Taglia",
        size_system: "Sistema taglia",
        condition: "Condizione",
        purchase_price: "Prezzo di acquisto",
        currency: "Valuta",
        purchase_date: "Data di acquisto",
        has_box: "Scatola originale",
        notes: "Note",
    };

    return labels[field] ?? field;
}


// Formatta un valore mostrato nel confronto prima/dopo di una modifica.
function formatUpdateValue(value) {
    if (value === null || value === undefined) {
        return "-";
    }

    if (value === true) {
        return "Yes";
    }

    if (value === false) {
        return "No";
    }

    return escapeHtml(value);
}


// Genera la card HTML compatta usata nei risultati dell'assistente.
function sneakerCardHtml(sneaker) {
    const condition = sneaker.condition;

    return `
        <div class="col-md-6 col-xl-4">
            <div class="card h-100">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <div class="text-secondary">
                                ${escapeHtml(sneaker.brand)}
                            </div>

                            <h3 class="card-title mb-1">
                                ${escapeHtml(sneaker.model)}
                            </h3>
                        </div>

                        ${
                            condition
                                ? `
                                    <span class="badge ${conditionBadgeClass(condition)}">
                                        ${escapeHtml(conditionLabel(condition))}
                                    </span>
                                `
                                : ""
                        }
                    </div>

                    <div class="text-secondary mb-3">
                        ${escapeHtml(sneaker.colorway)}
                    </div>

                    <div class="row g-2">
                        <div class="col-6">
                            <div class="text-secondary small">
                                Taglia
                            </div>

                            <strong>
                                ${
                                    sneaker.size !== null
                                        ? `${escapeHtml(sneaker.size)} ${escapeHtml(sneaker.size_system)}`
                                        : "-"
                                }
                            </strong>
                        </div>

                        <div class="col-6">
                            <div class="text-secondary small">
                                Prezzo
                            </div>

                            <strong>
                                ${
                                    sneaker.purchase_price !== null
                                        ? `${escapeHtml(sneaker.purchase_price)} ${escapeHtml(sneaker.currency)}`
                                        : "-"
                                }
                            </strong>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}


// Renderizza una lista di sneaker restituita dall'assistente.
function renderSneakerResults(data) {
    const container = document.getElementById("ai-response");
    const sneakers = data.result ?? [];

    if (sneakers.length === 0) {
        showMessage(
            data.response ?? "Nessuna sneaker trovata.",
            "info"
        );
        return;
    }

    const resultLabel = sneakers.length === 1
        ? "1 sneaker trovata"
        : `${sneakers.length} sneakers trovate`;

    container.innerHTML = `
        <div class="mb-3">
            <div class="d-flex align-items-center justify-content-between mb-3">
                <div>
                    <h3 class="mb-1">
                        Risultati
                    </h3>

                    <div class="text-secondary">
                        ${resultLabel}
                    </div>
                </div>
            </div>

            <div class="row row-cards">
                ${sneakers.map(sneakerCardHtml).join("")}
            </div>
        </div>
    `;
}


// Renderizza una singola sneaker restituita dall'assistente.
function renderSingleSneaker(data) {
    const container = document.getElementById("ai-response");

    if (!data.result) {
        showMessage(
            data.response ?? "Sneaker non trovata.",
            "info"
        );
        return;
    }

    container.innerHTML = `
        <div class="row row-cards">
            ${sneakerCardHtml(data.result)}
        </div>
    `;
}


// Renderizza la tabella principale della collezione.
function renderCollection(sneakers) {
    const tbody = document.getElementById("collection-body");

    if (sneakers.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-secondary">
                    Nessuna sneaker trovata.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = sneakers
        .map(sneaker => `
            <tr class="collection-row">
                <td>
                    ${escapeHtml(sneaker.brand)}
                </td>

                <td>
                    ${escapeHtml(sneaker.model)}
                </td>

                <td>
                    ${escapeHtml(sneaker.colorway)}
                </td>

                <td>
                    ${
                        sneaker.size !== null
                        && sneaker.size !== undefined
                            ? `${escapeHtml(sneaker.size)}
                               ${escapeHtml(sneaker.size_system)}`
                            : "-"
                    }
                </td>

                <td>
                    ${
                        sneaker.condition
                            ? `
                                <span
                                    class="badge ${conditionBadgeClass(
                                        sneaker.condition
                                    )}"
                                >
                                    ${escapeHtml(conditionLabel(sneaker.condition))}
                                </span>
                              `
                            : "-"
                    }
                </td>

                <td>
                    ${
                        sneaker.purchase_price !== null
                        && sneaker.purchase_price !== undefined
                            ? `${escapeHtml(sneaker.purchase_price)}
                               ${escapeHtml(sneaker.currency)}`
                            : "-"
                    }
                </td>

                <td class="text-end">
                    <button
                        class="btn btn-sm btn-outline-primary sneaker-details-btn"
                        data-sneaker-id="${sneaker.id}"
                        data-bs-toggle="modal"
                        data-bs-target="#sneaker-details-modal"
                    >
                        Dettagli
                    </button>
                </td>
            </tr>
        `)
        .join("");
}


// Mostra i dettagli completi della sneaker nel modal dedicato.
function renderSneakerDetails(sneaker) {
    const title = document.getElementById("details-title");
    const body = document.getElementById("details-body");

    title.textContent = `${sneaker.brand} ${sneaker.model}`;

    const boxValue = sneaker.has_box === true
        ? "Sì"
        : sneaker.has_box === false
            ? "No"
            : "-";

    const conditionHtml = sneaker.condition
        ? `
            <span class="badge ${conditionBadgeClass(sneaker.condition)}">
                ${escapeHtml(conditionLabel(sneaker.condition))}
            </span>
        `
        : "-";

    body.innerHTML = `
        <div class="sneaker-details-summary mb-4">
            <div>
                <div class="text-secondary small">
                    Colorway
                </div>

                <div class="h3 mb-0">
                    ${escapeHtml(sneaker.colorway)}
                </div>
            </div>

            ${conditionHtml}
        </div>

        <div class="row g-3">
            <div class="col-md-6">
                <div class="detail-field">
                    <div class="text-secondary small">Brand</div>
                    <strong>${escapeHtml(sneaker.brand)}</strong>
                </div>
            </div>

            <div class="col-md-6">
                <div class="detail-field">
                    <div class="text-secondary small">Modello</div>
                    <strong>${escapeHtml(sneaker.model)}</strong>
                </div>
            </div>

            <div class="col-md-6">
                <div class="detail-field">
                    <div class="text-secondary small">Taglia</div>
                    <strong>
                        ${
                            sneaker.size !== null
                                ? `${escapeHtml(sneaker.size)} ${escapeHtml(sneaker.size_system)}`
                                : "-"
                        }
                    </strong>
                </div>
            </div>

            <div class="col-md-6">
                <div class="detail-field">
                    <div class="text-secondary small">Style code</div>
                    <strong>${escapeHtml(sneaker.style_code)}</strong>
                </div>
            </div>

            <div class="col-md-6">
                <div class="detail-field">
                    <div class="text-secondary small">Prezzo di acquisto</div>
                    <strong>
                        ${
                            sneaker.purchase_price !== null
                                ? `${escapeHtml(sneaker.purchase_price)} ${escapeHtml(sneaker.currency)}`
                                : "-"
                        }
                    </strong>
                </div>
            </div>

            <div class="col-md-6">
                <div class="detail-field">
                    <div class="text-secondary small">Data di acquisto</div>
                    <strong>${escapeHtml(sneaker.purchase_date)}</strong>
                </div>
            </div>

            <div class="col-md-6">
                <div class="detail-field">
                    <div class="text-secondary small">Scatola originale</div>
                    <strong>${boxValue}</strong>
                </div>
            </div>

            <div class="col-md-6">
                <div class="detail-field">
                    <div class="text-secondary small">ID collezione</div>
                    <strong>#${escapeHtml(sneaker.id)}</strong>
                </div>
            </div>

            <div class="col-12">
                <div class="detail-field">
                    <div class="text-secondary small">Note</div>
                    <div>
                        ${escapeHtml(sneaker.notes)}
                    </div>
                </div>
            </div>
        </div>
    `;
}


// Carica e aggiorna le statistiche mostrate nella dashboard.
async function loadStats() {
    const response = await fetch("/stats");

    if (!response.ok) {
        throw new Error("Unable to load statistics");
    }

    const stats = await response.json();

    document.getElementById("total-pairs").textContent = stats.total_pairs;
    document.getElementById("total-brands").textContent = stats.total_brands;

    const spending = stats.spending_by_currency ?? [];

    if (spending.length === 0) {
        document.getElementById("total-spent").textContent = "0";
        return;
    }

    document.getElementById("total-spent").textContent = spending
        .map(item => `${item.total_spent} ${item.currency}`)
        .join(" · ");
}


// Carica la collezione dal backend e aggiorna la tabella locale.
async function loadCollection() {
    const response = await fetch("/sneakers");

    if (!response.ok) {
        throw new Error("Unable to load collection");
    }

    collectionCache = await response.json();
    renderCollection(collectionCache);
}


// Filtra localmente la collezione in base al testo inserito dall'utente.
function filterCollection(query) {
    const normalizedQuery = query.trim().toLowerCase();

    if (!normalizedQuery) {
        renderCollection(collectionCache);
        return;
    }

    const filtered = collectionCache.filter(sneaker => {
        const searchableFields = [
            sneaker.brand,
            sneaker.model,
            sneaker.colorway,
            sneaker.style_code,
            sneaker.condition,
            sneaker.size_system,
        ];

        return searchableFields.some(
            value =>
                value !== null
                && value !== undefined
                && String(value)
                    .toLowerCase()
                    .includes(normalizedQuery)
        );
    });

    renderCollection(filtered);
}


// Mostra un messaggio semplice nell'area di risposta dell'assistente.
function showMessage(message, type = "info") {
    const container = document.getElementById("ai-response");

    container.innerHTML = `
        <div class="alert alert-${type}">
            ${escapeHtml(message)}
        </div>
    `;
}


// Renderizza una risposta RAG insieme alle fonti utilizzate.
function renderRagResponse(data) {
    const container = document.getElementById("ai-response");
    const sources = data.result?.sources ?? [];

    let sourcesHtml = "";

    if (sources.length > 0) {
        sourcesHtml = `
            <div class="rag-sources mt-4">
                <div class="text-secondary small mb-2">
                    Fonte utilizzata
                </div>

                <div class="d-flex flex-wrap gap-2">
                    ${sources
                        .map(source => `
                            <span class="rag-source-chip">
                                ${escapeHtml(source.title)}
                            </span>
                        `)
                        .join("")}
                </div>
            </div>
        `;
    }

    container.innerHTML = `
        <div class="card rag-response-card">
            <div class="card-body">
                <div class="d-flex align-items-center justify-content-between mb-3">
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge bg-blue-lt text-blue">
                            Knowledge base
                        </span>

                        <span class="text-secondary small">
                            Risposta RAG
                        </span>
                    </div>
                </div>

                <div class="rag-answer">
                    ${escapeHtml(data.response)}
                </div>

                ${sourcesHtml}
            </div>
        </div>
    `;
}


// Renderizza la preview HITL per la modifica di una sneaker esistente.
function renderUpdatePreview(data) {
    pendingThreadId = data.thread_id;

    const preview = data.preview;
    const sneaker = preview.sneaker;
    const changes = preview.changes ?? [];
    const container = document.getElementById("ai-response");

    const changesHtml = changes
        .map(change => `
            <div class="col-12 col-lg-6">
                <div class="update-change-card">
                    <div class="text-secondary small mb-2">
                        ${escapeHtml(formatFieldName(change.field))}
                    </div>

                    <div class="update-values">
                        <div class="update-value-old">
                            <span class="text-secondary small">
                                Prima
                            </span>

                            <div>
                                ${formatUpdateValue(change.old)}
                            </div>
                        </div>

                        <div class="update-arrow">
                            →
                        </div>

                        <div class="update-value-new">
                            <span class="text-secondary small">
                                Dopo
                            </span>

                            <strong>
                                ${formatUpdateValue(change.new)}
                            </strong>
                        </div>
                    </div>
                </div>
            </div>
        `)
        .join("");

    container.innerHTML = `
        <div class="card hitl-card hitl-update-card">
            <div class="card-header">
                <div>
                    <div class="d-flex align-items-center gap-2 mb-1">
                        <span class="badge bg-blue-lt text-blue">
                            Modifica
                        </span>

                        <span class="text-secondary small">
                            Conferma richiesta
                        </span>
                    </div>

                    <h3 class="card-title mb-0">
                        ${escapeHtml(sneaker.brand)}
                        ${escapeHtml(sneaker.model)}
                    </h3>
                </div>
            </div>

            <div class="card-body">
                <p class="text-secondary mb-4">
                    Controlla le modifiche prima di aggiornare
                    la sneaker nella collezione.
                </p>

                <div class="row g-3">
                    ${changesHtml}
                </div>

                <div class="hitl-actions mt-4">
                    <button
                        id="cancel-update"
                        class="btn btn-outline-secondary"
                    >
                        Annulla
                    </button>

                    <button
                        id="confirm-update"
                        class="btn btn-primary"
                    >
                        Conferma modifica
                    </button>
                </div>
            </div>
        </div>
    `;

    document
        .getElementById("confirm-update")
        .addEventListener("click", () => confirmSneaker(true));

    document
        .getElementById("cancel-update")
        .addEventListener("click", () => confirmSneaker(false));
}


// Renderizza la preview HITL condivisa dai flussi di aggiunta ed eliminazione.
function renderPreview(data) {
    pendingThreadId = data.thread_id;

    const preview = data.preview;
    const container = document.getElementById("ai-response");
    const operation = data.confirmation?.operation ?? data.action;
    const isDelete = operation === "delete_sneaker";

    const title = isDelete
        ? `${escapeHtml(preview.brand)} ${escapeHtml(preview.model)}`
        : "Nuova sneaker";

    container.innerHTML = `
        <div class="card hitl-card ${isDelete ? "hitl-delete-card" : "hitl-add-card"}">
            <div class="card-header">
                <div>
                    <div class="d-flex align-items-center gap-2 mb-1">
                        <span class="badge ${isDelete ? "bg-red-lt text-red" : "bg-green-lt text-green"}">
                            ${isDelete ? "Eliminazione" : "Aggiunta"}
                        </span>

                        <span class="text-secondary small">
                            Conferma richiesta
                        </span>
                    </div>

                    <h3 class="card-title mb-0">
                        ${title}
                    </h3>
                </div>
            </div>

            <div class="card-body">
                ${
                    isDelete
                        ? `
                            <div class="alert alert-danger mb-4">
                                Questa sneaker verrà rimossa definitivamente
                                dalla tua collezione.
                            </div>
                        `
                        : `
                            <p class="text-secondary mb-4">
                                Controlla i dati prima di aggiungere
                                la sneaker alla collezione.
                            </p>
                        `
                }

                <div class="row g-3">
                    <div class="col-md-4">
                        <div class="text-secondary small">Brand</div>
                        <strong>${escapeHtml(preview.brand)}</strong>
                    </div>

                    <div class="col-md-4">
                        <div class="text-secondary small">Modello</div>
                        <strong>${escapeHtml(preview.model)}</strong>
                    </div>

                    <div class="col-md-4">
                        <div class="text-secondary small">Colorway</div>
                        <strong>${escapeHtml(preview.colorway)}</strong>
                    </div>

                    <div class="col-md-4">
                        <div class="text-secondary small">Taglia</div>
                        <strong>
                            ${
                                preview.size !== null
                                    ? `${escapeHtml(preview.size)} ${escapeHtml(preview.size_system)}`
                                    : "-"
                            }
                        </strong>
                    </div>

                    <div class="col-md-4">
                        <div class="text-secondary small">Condizione</div>
                        <strong>${escapeHtml(conditionLabel(preview.condition))}</strong>
                    </div>

                    <div class="col-md-4">
                        <div class="text-secondary small">Prezzo di acquisto</div>
                        <strong>
                            ${
                                preview.purchase_price !== null
                                    ? `${escapeHtml(preview.purchase_price)} ${escapeHtml(preview.currency)}`
                                    : "-"
                            }
                        </strong>
                    </div>

                    <div class="col-md-4">
                        <div class="text-secondary small">Style code</div>
                        <strong>${escapeHtml(preview.style_code)}</strong>
                    </div>

                    <div class="col-md-4">
                        <div class="text-secondary small">Scatola originale</div>
                        <strong>
                            ${
                                preview.has_box === true
                                    ? "Sì"
                                    : preview.has_box === false
                                        ? "No"
                                        : "-"
                            }
                        </strong>
                    </div>
                </div>

                <div class="hitl-actions mt-4">
                    <button
                        id="cancel-add"
                        class="btn btn-outline-secondary"
                    >
                        Annulla
                    </button>

                    <button
                        id="confirm-add"
                        class="${isDelete ? "btn btn-danger" : "btn btn-success"}"
                    >
                        ${isDelete ? "Elimina sneaker" : "Conferma aggiunta"}
                    </button>
                </div>
            </div>
        </div>
    `;

    document
        .getElementById("confirm-add")
        .addEventListener("click", () => confirmSneaker(true));

    document
        .getElementById("cancel-add")
        .addEventListener("click", () => confirmSneaker(false));
}


// Renderizza le possibili sneaker quando un'eliminazione è ambigua.
function renderDeleteChoices(data) {
    const container = document.getElementById("ai-response");
    const sneakers = data.result ?? [];

    const choicesHtml = sneakers
        .map(sneaker => `
            <div class="delete-choice-card">
                <div>
                    <div class="d-flex align-items-center gap-2 mb-1">
                        <strong>
                            ${escapeHtml(sneaker.brand)}
                            ${escapeHtml(sneaker.model)}
                        </strong>

                        <span class="badge bg-secondary-lt">
                            ID ${escapeHtml(sneaker.id)}
                        </span>
                    </div>

                    <div class="text-secondary small">
                        ${escapeHtml(sneaker.colorway)}
                        ${
                            sneaker.size !== null
                                ? ` · ${escapeHtml(sneaker.size)} ${escapeHtml(sneaker.size_system)}`
                                : ""
                        }
                        ${
                            sneaker.purchase_price !== null
                                ? ` · ${escapeHtml(sneaker.purchase_price)} ${escapeHtml(sneaker.currency)}`
                                : ""
                        }
                    </div>
                </div>

                <button
                    type="button"
                    class="btn btn-sm btn-outline-danger delete-choice"
                    data-sneaker-id="${sneaker.id}"
                >
                    Seleziona
                </button>
            </div>
        `)
        .join("");

    container.innerHTML = `
        <div class="card hitl-card hitl-delete-card">
            <div class="card-header">
                <div>
                    <div class="d-flex align-items-center gap-2 mb-1">
                        <span class="badge bg-red-lt text-red">
                            Eliminazione
                        </span>

                        <span class="text-secondary small">
                            Selezione richiesta
                        </span>
                    </div>

                    <h3 class="card-title mb-0">
                        Quale sneaker vuoi eliminare?
                    </h3>
                </div>
            </div>

            <div class="card-body">
                <p class="text-secondary">
                    Ho trovato ${sneakers.length} sneakers corrispondenti.
                </p>

                <div class="d-flex flex-column gap-2">
                    ${choicesHtml}
                </div>
            </div>
        </div>
    `;

    container
        .querySelectorAll(".delete-choice")
        .forEach(button => {
            button.addEventListener("click", () => {
                const input = document.getElementById("ai-input");

                input.value =
                    `Elimina la sneaker con ID ${button.dataset.sneakerId}`;

                sendAIMessage();
            });
        });
}


// Invia una richiesta in linguaggio naturale all'endpoint dell'assistente.
async function sendAIMessage() {
    const input = document.getElementById("ai-input");
    const button = document.getElementById("ai-send");
    const text = input.value.trim();

    if (text.length < 3) {
        showMessage(
            "Write a longer request.",
            "warning"
        );
        return;
    }

    button.disabled = true;
    showMessage(
        "Processing request...",
        "info"
    );

    try {
        const response = await fetch(
            "/ai/chat",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    text: text,
                }),
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ?? "AI request failed"
            );
        }

        input.value = "";

        if (
            data.status === "awaiting_confirmation"
            && data.preview
        ) {
            const operation = data.confirmation?.operation ?? data.action;

            if (operation === "update_sneaker") {
                renderUpdatePreview(data);
            } else {
                renderPreview(data);
            }

            return;
        }

        if (
            (
                data.action === "search_collection"
                || data.action === "list_collection"
            )
            && Array.isArray(data.result)
        ) {
            renderSneakerResults(data);
            return;
        }

        if (data.action === "sneaker_by_id") {
            renderSingleSneaker(data);
            return;
        }

        if (
            data.action === "sneaker_knowledge"
            && data.status === "completed"
        ) {
            pendingThreadId = null;
            renderRagResponse(data);
            return;
        }

        if (
            data.action === "delete_sneaker"
            && data.status === "ambiguous"
            && Array.isArray(data.result)
        ) {
            renderDeleteChoices(data);
            return;
        }

        pendingThreadId = null;
        showMessage(
            data.response ?? "Request completed.",
            "success"
        );
    } catch (error) {
        console.error(error);
        showMessage(
            error.message,
            "danger"
        );
    } finally {
        button.disabled = false;
    }
}


// Conferma o annulla l'operazione HITL attualmente in sospeso.
async function confirmSneaker(approved) {
    if (!pendingThreadId) {
        showMessage(
            "No pending confirmation found.",
            "warning"
        );
        return;
    }

    const threadId = pendingThreadId;

    showMessage(
        approved
            ? "Saving sneaker..."
            : "Cancelling...",
        "info"
    );

    try {
        const response = await fetch(
            "/ai/confirm",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    thread_id: threadId,
                    approved: approved,
                }),
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ?? "Confirmation failed"
            );
        }

        pendingThreadId = null;

        if (SUCCESSFUL_CONFIRMATION_STATUSES.has(data.status)) {
            showMessage(
                data.response,
                "success"
            );

            await Promise.all([
                loadStats(),
                loadCollection(),
            ]);
            return;
        }

        if (data.status === "cancelled") {
            showMessage(
                data.response,
                "secondary"
            );
            return;
        }

        showMessage(
            data.response ?? "Operation completed.",
            "info"
        );
    } catch (error) {
        console.error(error);
        showMessage(
            error.message,
            "danger"
        );
    }
}


// Collega i controlli dell'assistente ai rispettivi handler.
function bindAssistantEvents() {
    document
        .getElementById("ai-send")
        .addEventListener("click", sendAIMessage);

    document
        .getElementById("ai-input")
        .addEventListener("keydown", event => {
            if (event.key === "Enter") {
                sendAIMessage();
            }
        });

    document
        .querySelectorAll(".ai-suggestion")
        .forEach(button => {
            button.addEventListener("click", () => {
                const input = document.getElementById("ai-input");

                input.value = button.dataset.prompt;
                input.focus();
            });
        });
}


// Collega ricerca e apertura dei dettagli agli elementi della collezione.
function bindCollectionEvents() {
    document
        .getElementById("collection-search")
        .addEventListener("input", event => {
            filterCollection(event.target.value);
        });

    document
        .getElementById("collection-body")
        .addEventListener("click", event => {
            const button = event.target.closest(".sneaker-details-btn");

            if (!button) {
                return;
            }

            const sneakerId = Number(button.dataset.sneakerId);
            const sneaker = collectionCache.find(
                item => item.id === sneakerId
            );

            if (!sneaker) {
                return;
            }

            renderSneakerDetails(sneaker);
        });
}


// Inizializza i dati della dashboard e registra gli event listener della pagina.
async function initializeDashboard() {
    try {
        await Promise.all([
            loadStats(),
            loadCollection(),
        ]);
    } catch (error) {
        console.error(
            "Error loading dashboard:",
            error
        );
    }

    bindAssistantEvents();
    bindCollectionEvents();
}


document.addEventListener(
    "DOMContentLoaded",
    initializeDashboard
);
