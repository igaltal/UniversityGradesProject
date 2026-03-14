document.addEventListener("DOMContentLoaded", function () {
    // Color the average value
    var el = document.getElementById("average");
    if (el) {
        var avg = parseFloat(el.textContent);
        if (isNaN(avg) || avg === 0) el.style.color = "#6b7280";
        else if (avg >= 85)          el.style.color = "#16a34a";
        else if (avg >= 70)          el.style.color = "#d97706";
        else                         el.style.color = "#dc2626";
    }

    // Poll scraper status on dashboard (always poll to catch periodic checks)
    var banner  = document.getElementById("scraper-banner");
    var msg     = document.getElementById("scraper-msg");
    var spinner = document.getElementById("scraper-spinner");
    if (!banner) return;

    var pollInterval = 3000;  // ms between polls

    function poll() {
        fetch("/scraper-status")
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (!data.message) {
                    banner.className = "scraper-banner scraper-hidden";
                    setTimeout(poll, pollInterval);
                    return;
                }

                msg.textContent = data.message;

                if (data.running) {
                    banner.className = "scraper-banner scraper-running";
                    spinner.classList.remove("hidden");
                    setTimeout(poll, 2000);
                } else if (data.last_result === "success") {
                    banner.className = "scraper-banner scraper-success";
                    spinner.classList.add("hidden");
                    setTimeout(function () { location.reload(); }, 1500);
                } else if (data.last_result === "error") {
                    banner.className = "scraper-banner scraper-error";
                    spinner.classList.add("hidden");
                    setTimeout(poll, pollInterval);
                } else {
                    setTimeout(poll, pollInterval);
                }
            })
            .catch(function () {
                setTimeout(poll, 5000);
            });
    }

    // Start polling (catches both initial and periodic scrape updates)
    setTimeout(poll, 1000);
});
