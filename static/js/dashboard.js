const dashboardRoot = document.getElementById("dashboardRoot");

if (dashboardRoot) {

    const urls = {
        daily: dashboardRoot.dataset.salesUrlDaily,
        weekly: dashboardRoot.dataset.salesUrlWeekly,
        monthly: dashboardRoot.dataset.salesUrlMonthly
    };

    let chartInstance = null;

    function loadChart(period) {

        fetch(urls[period])
            .then(response => response.json())
            .then(data => {

                const canvas = document.getElementById("salesChart");

                if (!canvas) return;

                if (chartInstance) {
                    chartInstance.destroy();
                }

                chartInstance = new Chart(canvas, {

                    type: "bar",

                    data: {

                        labels: data.map(item => item.day),

                        datasets: [{
                            label: "Sales (₹)",
                            data: data.map(item => item.total),
                            backgroundColor: "#c1622d",
                            borderRadius: 6
                        }]
                    },

                    options: {

                        responsive: true,

                        maintainAspectRatio: false,

                        plugins: {

                            legend: {
                                display: false
                            }

                        },

                        scales: {

                            y: {
                                beginAtZero: true
                            }

                        }

                    }

                });

            })

            .catch(err => console.error(err));

    }

    document.querySelectorAll("[data-period]").forEach(button => {

        button.addEventListener("click", function () {

            document.querySelectorAll("[data-period]").forEach(btn => {

                btn.classList.remove("active");

            });

            this.classList.add("active");

            loadChart(this.dataset.period);

        });

    });

    loadChart("daily");

    // Category-wise revenue chart — data is already scoped server-side
    // (cashiers see only their own sales, admins see everyone's).
    const categoryCanvas = document.getElementById("categoryChart");
    const categoryUrl = dashboardRoot.dataset.salesUrlCategory;

    if (categoryCanvas && categoryUrl) {
        const palette = ["#c1622d", "#4a7c59", "#7a3b2e", "#d9a544", "#8a8478", "#b3452c", "#5c2c22", "#a54f22"];

        fetch(categoryUrl)
            .then(response => response.json())
            .then(data => {
                if (!data.length) {
                    categoryCanvas.parentElement.innerHTML = '<p class="text-muted text-center mb-0">No category sales yet.</p>';
                    return;
                }
                new Chart(categoryCanvas, {
                    type: "doughnut",
                    data: {
                        labels: data.map(item => item.category),
                        datasets: [{
                            data: data.map(item => item.total),
                            backgroundColor: data.map((_, i) => palette[i % palette.length])
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: "bottom",
                                labels: { boxWidth: 14, font: { size: 11 } }
                            }
                        }
                    }
                });
            })
            .catch(err => console.error(err));
    }

}
