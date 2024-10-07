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
