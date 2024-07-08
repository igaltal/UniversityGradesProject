document.addEventListener("DOMContentLoaded", function() {
    const averageElement = document.getElementById('average');
    const average = parseFloat(averageElement.textContent);

    if (average >= 85) {
        averageElement.style.color = 'green';
    } else if (average >= 70) {
        averageElement.style.color = 'orange';
    } else {
        averageElement.style.color = 'red';
    }
});
