$(document).ready(function() {
    // Smooth scrolling for internal links
    $('a.nav-link').click(function(event) {
        var target = $(this).attr('href');
        if (target.startsWith('#')) {
            event.preventDefault();
            $('html, body').animate({
                scrollTop: $(target).offset().top
            }, 800);
        }
    });
});
 document.addEventListener("DOMContentLoaded", function() {
        const items = document.querySelectorAll('.testimonial-item');
        let currentIndex = 0;

        function showItem(index) {
            items.forEach((item, i) => {
                item.classList.remove('active');
                if (i === index) {
                    item.classList.add('active');
                }
            });
        }

        function nextItem() {
            currentIndex = (currentIndex + 1) % items.length;
            showItem(currentIndex);
        }

        // Initial display
        showItem(currentIndex);
        setInterval(nextItem, 5000); // Change slide every 5 seconds
    });




     document.addEventListener("DOMContentLoaded", function() {
        const counters = document.querySelectorAll('.counter-number');
        let isCounterAnimated = false;

        function animateCounters() {
            if (isCounterAnimated) return; // Prevents counting again

            counters.forEach(counter => {
                const updateCount = () => {
                    const target = +counter.getAttribute('data-count'); // Get target count
                    const count = +counter.innerText; // Get current count
                    const increment = Math.ceil(target / 200); // Determine increment

                    if (count < target) {
                        counter.innerText = count + increment; // Update counter
                        setTimeout(updateCount, 1); // Call function again
                    } else {
                        counter.innerText = target; // Ensure it reaches the target
                    }
                };

                updateCount();
            });

            isCounterAnimated = true; // Set flag to true after animation
        }

        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounters();
                    observer.unobserve(entry.target); // Stop observing after animation
                }
            });
        });

        observer.observe(document.querySelector('.counter-section')); // Observe the counter section
    });