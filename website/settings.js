let supervisors = [];
async function loadSupervisors() {
    supervisors = check_response(await get_supervisors());

    let list = document.getElementById("supervisor-list");
    
    while (list.children.length) {
        list.removeChild(list.children[0]);
    }

    if (supervisors.length == 0) {
        const elem = document.createElement("li");
        elem.innerText = "You haven't added anyone yet";
        elem.classList.add("no-supervisors");

        list.appendChild(elem);
    } else {
        for (const supervisor of supervisors) {
            const elem = document.createElement("li");
            elem.innerText = supervisor + " ";
            elem.classList.add("supervisor-name");

            const removeLink = document.createElement("a");
            removeLink.innerText = "remove";
            removeLink.onclick = () => {
                if (confirm("Are you sure you want to remove " + supervisor + " as a supervisor?")){
                    removeSupervisorButtonPress(supervisor);
                }
            }
            removeLink.href = "javascript:void(0)"

            elem.appendChild(removeLink);

            list.appendChild(elem);
        }
    }
}

async function settingsLoad() {
    await loadSupervisors();
}

async function removeSupervisorButtonPress(name) {
    await remove_supervisor(name);
    loadSupervisors();
}

async function addSupervisorButtonPress() {
    const name = document.getElementById("new-supervisor-name").value;
    res = await add_supervisor(name);
    console.log(res.ok);
    console.log(supervisors);
    if (!res.ok) {
        alert("Supervisor username does not exist. Please enter a valid username.");
    }
    else {
        alert("Supervisor added successfully!");
    }
    document.getElementById("new-supervisor-name").value = "";
    loadSupervisors();
}