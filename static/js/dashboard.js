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

}