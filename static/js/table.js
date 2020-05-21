var $TABLE = $('#table');
var $BTN = $('#export-btn');
var $BTN2 = $('#update-btn');
var $EXPORT = $('#export');

var $CART = $('#cart');
var $BTN3 = $('#confirm-btn');

$('.table-add-inventory').click(function () {
  var $clone = $TABLE.find('tr.hide').clone(true).removeClass('hide table-line');
  /*$TABLE.find('table').append($clone);*/ /*prepend*/
    $TABLE.find('table tr:first').after($clone);
});

$('.table-add-comment').click(function () {
    var $clone = $TABLE.find('tr.hide').clone(true).removeClass('hide table-line');
    $TABLE.find('table').append($clone);
});

$('.table-remove').click(function () {
  $(this).parents('tr').detach();
});

$('.table-up').click(function () {
  var $row = $(this).parents('tr');
  if ($row.index() === 1) return; // Don't go above the header
  $row.prev().before($row.get(0));
});

$('.table-down').click(function () {
  var $row = $(this).parents('tr');
  $row.next().after($row.get(0));
});

// A few jQuery helpers for exporting only
jQuery.fn.pop = [].pop;
jQuery.fn.shift = [].shift;

$BTN.click(function () {
  var $rows = $TABLE.find('tr:not(:hidden)');
  var headers = [];
  var data = [];
  
  // Get the headers (add special header logic here)
  $($rows.shift()).find('th:not(:empty)').each(function () {
    headers.push($(this).text().toLowerCase());
  });
  
  // Turn all existing rows into a loopable array
  $rows.each(function () {
    var $td = $(this).find('td');
    var h = {};
    
    // Use the headers from earlier to name our hash keys
    headers.forEach(function (header, i) {
      h[header] = $td.eq(i).text();   
    });
    
    data.push(h);
  });
  
  // Output the result
    $EXPORT.text(JSON.stringify(data));

    localStorage.setItem('#export', JSON.stringify(data));

    $.post("/postmethod", {
        javascript_data: JSON.stringify(data)
    });

    window.location.reload(true);

});

$BTN2.click(function () {

    window.location.reload(true); 

})

$BTN3.click(function () {

    var elements = document.documentElement.innerHTML;

    localStorage.setItem('#export', elements);

    $.post("/postmethod", {
        javascript_data: elements
    });

    window.location.reload(true);

})