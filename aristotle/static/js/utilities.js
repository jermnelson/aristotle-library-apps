function add_member() {
 var row_num = $('#rule-table tr:last').prevAll().length + 1;
 var new_row = '<tr><td>' + row_num + '</td>'
 new_row += '<td><textarea class="skos_rule" disabled="disabled">' + $('#skos_rule').val() + '</textarea></td>';
 new_row += '<td><a href="#" onclick="remove_rule(' + "'" + row_num + "'";
 new_row += ')" class="btn"><i class="icon-minus"></i> Remove</a></td></tr>';
 $('#rule-table tr:last').after(new_row);
 $('#skos_rule').attr('value','');
 $('#add-member').modal('hide');
}

function remove_rule(row_num) {
  $('#rule-table tr').index(row_num).remove();
}

function reset_map() {
  $('#frbr-entity').val('NONE');
  $('#frbr-entity-property-name').attr('value','');
  $('#frbr-entity-property-uri').attr('value','');
  $('#metadata-schema').attr('value','');
  $('#metadata-schema-uri').attr('value','');
  $('#orderedCollection').attr('checked',false);
  $('#skos_rule').attr('value','');
  $('#rule-table').find('tr:gt(0)').remove();
}

function save_map() {
  var data = 'entity=' + $('#frbr-entity option:selected').val();
  data += '&prop=' + $('#frbr-entity-property-name').val();
  data += '&propuri=' + $('#frbr-entity-property-uri').val();
  data += '&schema=' + $('#metadata-schema').val();
  data += '&schemauri=' + $('#metadata-schema-uri').val();
  if($('#orderedCollection').attr('checked')) { 
    data += '&ordered=True';
  }
  $('.skos_rule').each(function() {
	  data += '&rule=' + $(this).val();
	});
  alert(data);
  $.ajax({
	  data: data,
	  url: '/utilities/skos/save',
	  type: 'POST',
	  success: function(data) {
		alert(data);
		reset_map();  
	  }
   });
}
