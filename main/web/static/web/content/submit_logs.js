(function($){
    var localpath = window.location.pathname, csrfmiddlewaretoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    $("li.nav-item.submit_logs-menu").addClass("active");
})(jQuery);