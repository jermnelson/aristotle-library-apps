function all_apps_view() {
 $.ajax({
    url: '/apps/portfolio/json',
   type: 'get',
   data: 'func=all_apps_view',
   success: function(response_html) {
     $("#main-pane").val(response_html);
     $("#all-app-view-id").attr("class","btn disabled");
     $("#dis-access-view").attr("class","btn");
     $("#productivity-view").attr("class","btn");
  }
 });
}

function dis_access_view() {
 $("#dis-access-view").attr("class","btn disabled");
 $("#all-app-view-id").attr("class","btn");
 $("#productivity-view").attr("class","btn");
}

function pro_view() {
 $("#all-app-view-id").attr("class","btn");
 $("#productivity-view").attr("class","btn disabled");
 $("#all-app-view-id").attr("class","btn");

}
