//
// Homelab Control Center V2
// dashboard.js
//


let proxmoxOnline = false;

let activityLog = [];

let hostDetailsOpen = false;

let hostMetricsInterval = null;

let vmDetailsIntervals = {};

let pendingHostAction = null;

let refreshFailed = false;


//
// Theme
//

function initializeTheme() {

    const savedTheme =
        localStorage.getItem(
            "theme"
        );

    if (
        savedTheme === "light"
    ) {

        document.body
            .classList
            .add(
                "light"
            );

    }

    const button =
        document.getElementById(
            "themeToggle"
        );

    button.addEventListener(
        "click",
        toggleTheme
    );

}

function toggleTheme() {

    document.body
        .classList
        .toggle(
            "light"
        );

    localStorage.setItem(

        "theme",

        document.body
            .classList
            .contains(
                "light"
            )
        ? "light"
        : "dark"

    );

}


//
// Activity Log
//

function addActivity(
    message
) {

    const timestamp =
        new Date()
        .toLocaleString();

    activityLog.unshift(
        `${timestamp}  ${message}`
    );

    if (
        activityLog.length > 27
    ) {

        activityLog =
            activityLog.slice(
                0,
                27
            );

    }

    renderActivityLog();

}

function renderActivityLog() {

    const container =
        document.getElementById(
            "activityLog"
        );

    container.innerHTML =

        activityLog
            .map(
                entry =>
                    `<div class="activity-entry">${entry}</div>`
            )
            .join("");

}


//
// Refresh Timestamp
//

function updateRefreshTimestamp() {

    document
        .getElementById(
            "lastRefresh"
        )
        .innerText =

        new Date()
        .toLocaleString();

}

function setRefreshFailed() {

    refreshFailed = true;

    document
        .getElementById(
            "staleWarning"
        )
        .innerHTML =

        `
        <span class="warning">
            Refresh Failed
        </span>
        `;

}

function clearRefreshFailed() {

    refreshFailed = false;

    document
        .getElementById(
            "staleWarning"
        )
        .innerHTML = "";

}


//
// Infrastructure
//

async function refreshStatus() {

    try {

        const response =
            await fetch(
                "/api/status"
            );

        const data =
            await response.json();

        proxmoxOnline =
            data.proxmox_online;

        document
            .getElementById(
                "status"
            )
            .innerHTML =

            `
            Router:
            <span class="${
                data.router_online
                ? "online"
                : "offline"
            }">

                ${
                    data.router_online
                    ? "Online"
                    : "Offline"
                }

            </span>

            <br><br>

            Proxmox:
            <span class="${
                data.proxmox_online
                ? "online"
                : "offline"
            }">

                ${
                    data.proxmox_online
                    ? "Online"
                    : "Offline"
                }

            </span>
            `;

        clearRefreshFailed();

        updateRefreshTimestamp();

    }

    catch {

        setRefreshFailed();

    }

}


//
// Master Refresh
//

async function refreshAll() {

    await refreshStatus();

    await refreshVMs();

    renderHostCard();

}


//
// Scheduler
//

function startRefreshScheduler() {

    //
    // Immediate
    //

    refreshAll();

    //
    // 10 seconds later
    //

    setTimeout(

        refreshAll,

        10000

    );

    //
    // Every minute
    //

    setInterval(

        refreshAll,

        60000

    );

}


//
// Startup
//

document.addEventListener(

    "DOMContentLoaded",

    function() {

        initializeTheme();

        startRefreshScheduler();

        addActivity(
            "✓ Dashboard started"
        );

    }

);


function renderHostCard() {

    const card =
        document.getElementById(
            "hostCard"
        );

    if (
        !proxmoxOnline
    ) {

        clearHostMetricsPolling();

        card.innerHTML =

        `
        <h2>
            🖥 Proxmox Host
        </h2>

        <div>

            Status:
            <span class="offline">
                Offline
            </span>

        </div>

        <br>

        <div class="toggle-row">

            Power

            <label class="switch">

                <input
                    type="checkbox"

                    onchange="
                        hostPowerOn()
                    ">

                <span class="slider">
                </span>

            </label>

        </div>
        `;

        return;

    }

    card.innerHTML =

    `
    <h2>
        🖥 Proxmox Host
    </h2>

    <div id="hostStatusText">

        Status:
        <span class="online">
            Online
        </span>

    </div>

    <br>

    <div class="toggle-row">

        Power

        <label class="switch">

            <input
                checked
                type="checkbox"

                onchange="
                    hostPowerOff()
                ">

            <span class="slider">
            </span>

        </label>

    </div>

    <br>

    <button
        class="reboot-btn"

        onclick="
            openHostConfirmModal(
                'reboot'
            )
        ">

        Reboot

    </button>

    <button
        class="details-btn"

        onclick="
            toggleHostDetails()
        ">

        More Details

    </button>

    <div
        id="hostDetailsContainer"
        class="
            details-container
            ${hostDetailsOpen ? 'open' : ''}
        ">

        <div
            id="hostDetails"
            class="details-panel">

        </div>

    </div>
    `;

    if (
        hostDetailsOpen
    ) {

        loadHostDetails();

    }

}

//
// Host Details
//

async function loadHostDetails() {

    const details =
        document.getElementById(
            "hostDetails"
        );

    if (!details) {
        return;
    }

    try {

        const response =
            await fetch(
                "/api/proxmox/details"
            );

        const data =
            await response.json();

        //
        // First render only
        //

        if (
            details.innerHTML.trim() === ""
        ) {

            details.innerHTML =

            `
            <div class="metric-row">
                <span>CPU Usage</span>
                <span id="host-cpu">--</span>
            </div>

            <div class="metric-row">
                <span>RAM Usage</span>
                <span id="host-ram">--</span>
            </div>

            <div class="metric-row">
                <span>Disk Usage</span>
                <span id="host-disk">--</span>
            </div>

            <div class="metric-row">
                <span>Uptime</span>
                <span id="host-uptime">--</span>
            </div>

            <div class="metric-row">
                <span>IP Address</span>
                <span id="host-ip">--</span>
            </div>
            `;
        }

        //
        // Update values only
        //

        document.getElementById(
            "host-cpu"
        ).innerText =
            data.cpu_percent + "%";

        document.getElementById(
            "host-ram"
        ).innerText =
            data.ram_percent + "%";

        document.getElementById(
            "host-disk"
        ).innerText =
            data.disk_percent + "%";

        document.getElementById(
            "host-uptime"
        ).innerText =
            data.uptime;

        document.getElementById(
            "host-ip"
        ).innerText =
            data.ip;

    }

    catch (error) {

        console.error(
            "Failed to load host details",
            error
        );

    }

}

function clearHostMetricsPolling() {

    if (
        hostMetricsInterval
    ) {

        clearInterval(
            hostMetricsInterval
        );

        hostMetricsInterval =
            null;

    }

}

function startHostMetricsPolling() {

    clearHostMetricsPolling();

    hostMetricsInterval =

        setInterval(

            loadHostDetails,

            2000

        );

}

function toggleHostDetails() {

    hostDetailsOpen =
        !hostDetailsOpen;

    renderHostCard();

    if (
        hostDetailsOpen
    ) {

        loadHostDetails();

        startHostMetricsPolling();

    }

    else {

        clearHostMetricsPolling();

    }

}

//
// Host Power
//

async function hostPowerOn() {

    addActivity(
        "⏳ Sending wake command..."
    );

    await fetch(

        "/api/host/wake",

        {
            method: "POST"
        }

    );

    addActivity(
        "✓ Wake command sent"
    );

}

function hostPowerOff() {

    openHostConfirmModal(
        "suspend"
    );

}

//
// Modal
//

function openHostConfirmModal(
    action
) {

    pendingHostAction =
        action;

    document
        .getElementById(
            "confirmInput"
        )
        .value = "";

    document
        .getElementById(
            "confirmModalButton"
        )
        .disabled = true;

    document
        .getElementById(
            "confirmModal"
        )
        .style.display =
        "flex";

}

function closeConfirmModal() {

    document
        .getElementById(
            "confirmModal"
        )
        .style.display =
        "none";

    renderHostCard();

}

document
    .getElementById(
        "cancelModalButton"
    )
    .addEventListener(

        "click",

        closeConfirmModal

    );

document
    .getElementById(
        "confirmInput"
    )
    .addEventListener(

        "input",

        function() {

            document
                .getElementById(
                    "confirmModalButton"
                )
                .disabled =

                this.value !==
                "confirm";

        }

    );

document
    .getElementById(
        "confirmModalButton"
    )
    .addEventListener(

        "click",

        async function() {

            closeConfirmModal();

            addActivity(

                `⏳ Host ${pendingHostAction} requested`

            );

            await fetch(

                `/api/host/${pendingHostAction}`,

                {
                    method: "POST"
                }

            );

            addActivity(

                `✓ Host ${pendingHostAction} initiated`

            );

        }

    );

let vmDataCache = {};


//
// VM Rendering
//

async function refreshVMs() {

	for (const vmid in vmDetailsIntervals) {

 		clearInterval(
	        	vmDetailsIntervals[vmid]
    		);
	}
	vmDetailsIntervals = {};

	if (!proxmoxOnline) {

        document.getElementById(
            "vmContainer"
        ).innerHTML = "";

        return;
    }

    try {

        const response =
            await fetch(
                "/api/vms"
            );

        const data =
            await response.json();

        vmDataCache = {};

        data.vms.forEach(
            vm => {

                vmDataCache[
                    vm.vmid
                ] = vm;

            }
        );

        renderVMCards(
            data.vms
        );

    }

    catch {

        document.getElementById(
            "vmContainer"
        ).innerHTML =

        `
        <div class="card">
            Failed to load VMs
        </div>
        `;

    }

}

function renderVMCards(vms) {

    const container =
        document.getElementById(
            "vmContainer"
        );

    let html = "";

    for (const vm of vms) {

        const running =
            vm.status ===
            "running";

        html +=

        `
        <div
            class="card"
            id="vm-card-${vm.vmid}">

            <h3>
                ${vm.name}
            </h3>

            <div
                id="vm-status-${vm.vmid}">

                Status:

                <span class="
                    ${running
                        ? "online"
                        : "offline"}
                ">

                    ${vm.status}

                </span>

            </div>

            <br>

            <div class="toggle-row">

                Power

                <label class="switch">

                    <input

                        ${
                            running
                            ? "checked"
                            : ""
                        }

                        type="checkbox"

                        onchange="
                            vmPowerToggle(
                                ${vm.vmid},
                                '${vm.name}',
                                ${running},
                                this
                            )
                        ">

                    <span class="slider">
                    </span>

                </label>

            </div>

            <br>

            <button
                class="reboot-btn"

                onclick="
                    rebootVm(
                        ${vm.vmid},
                        '${vm.name}'
                    )
                ">

                Reboot

            </button>

            <button
                class="details-btn"

                onclick="
                    toggleVmDetails(
                        ${vm.vmid}
                    )
                ">

                More Details

            </button>

            <div
                id="vm-details-container-${vm.vmid}"
                class="details-container">

                <div
                    id="vm-details-${vm.vmid}"
                    class="details-panel">

                </div>

            </div>

        </div>
        `;
    }

    container.innerHTML =
        html;

}

//
// VM Details
//

function toggleVmDetails(vmid) {

    const container =
        document.getElementById(
            `vm-details-container-${vmid}`
        );

    const isOpen =
        container.classList.contains(
            "open"
        );

    if (isOpen) {

        container.classList.remove(
            "open"
        );

        stopVmPolling(
            vmid
        );

        return;
    }

    container.classList.add(
        "open"
    );

    loadVmDetails(
        vmid
    );

    startVmPolling(
        vmid
    );

}

async function loadVmDetails(vmid) {

    const panel =
        document.getElementById(
            `vm-details-${vmid}`
        );

    if (!panel) {
        return;
    }

    panel.innerHTML =

    `
    <div class="loading">
        Loading...
    </div>
    `;

    try {

        const response =
            await fetch(
                `/api/vm/${vmid}/details`
            );

        const data =
            await response.json();

        panel.innerHTML =

        `
        <div class="metric-row">
            <span>VMID</span>
            <span>${data.vmid}</span>
        </div>

        <div class="metric-row">
            <span>Status</span>
            <span>${data.status}</span>
        </div>

        <div class="metric-row">
            <span>IP Address</span>
            <span>${data.ip}</span>
        </div>
        `;

    }

    catch {

        panel.innerHTML =

        `
        <div class="warning">
            Failed to load details
        </div>
        `;

    }

}

function startVmPolling(vmid) {

    stopVmPolling(vmid);

    vmDetailsIntervals[
        vmid
    ] = setInterval(

        function() {

            loadVmDetails(
                vmid
            );

        },

        2000

    );

}

function stopVmPolling(vmid) {

    if (
        vmDetailsIntervals[
            vmid
        ]
    ) {

        clearInterval(

            vmDetailsIntervals[
                vmid
            ]

        );

        delete vmDetailsIntervals[
            vmid
        ];

    }

}

//
// VM Actions
//

async function vmPowerToggle(
    vmid,
    name,
    running,
    toggleElement
) {

    if (running) {

        if (
            !confirm(
                `Stop VM ${name}?`
            )
        ) {

            //
            // Immediate snapback fix
            //

            toggleElement.checked =
                true;

            return;
        }

        addActivity(
            `⏳ Shutting down ${name}...`
        );

        setVmPendingState(
            vmid,
            "Shutting Down..."
        );

        await fetch(

            `/api/vm/${vmid}/stop`,

            {
                method: "POST"
            }

        );

        addActivity(
            `✓ ${name} shutdown initiated`
        );

    }

    else {

        addActivity(
            `⏳ Starting ${name}...`
        );

        setVmPendingState(
            vmid,
            "Starting..."
        );

        await fetch(

            `/api/vm/${vmid}/start`,

            {
                method: "POST"
            }

        );

        addActivity(
            `✓ ${name} start initiated`
        );

    }

    setTimeout(
        refreshAll,
        1000
    );

}

async function rebootVm(
    vmid,
    name
) {

    if (
        !confirm(
            `Reboot VM ${name}?`
        )
    ) {

        return;
    }

    addActivity(
        `⏳ Rebooting ${name}...`
    );

    setVmPendingState(
        vmid,
        "Rebooting..."
    );

    await fetch(

        `/api/vm/${vmid}/reboot`,

        {
            method: "POST"
        }

    );

    addActivity(
        `✓ ${name} reboot initiated`
    );

    setTimeout(
        refreshAll,
        1000
    );

}

//
// Pending State
//

function setVmPendingState(
    vmid,
    message
) {

    const statusDiv =
        document.getElementById(
            `vm-status-${vmid}`
        );

    if (!statusDiv) {
        return;
    }

    statusDiv.innerHTML =

    `
    Status:

    <span class="pending">
        ${message}
    </span>
    `;

}
