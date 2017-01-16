/**
 * Created by chiel on 15-1-17.
 */
$('document').ready(function(){

    $('.trip-info').click(function() {
        var details = $('.trip-details', this);
        details.toggle('slow'); // p00f
        details.find($('.line')).last().hide();
    });
});