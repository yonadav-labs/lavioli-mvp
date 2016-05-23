function search_residental(form_id)
{
  $.post('/residential/properties/', $('#'+form_id).serialize())
  .success(function(result){
    $('.middle').html(result);
  });
}

function login_check(e, logged_in)
{
  if (logged_in === 'False')
  {
    e.stopPropagation();    
    $( "#dialog-confirm" ).dialog({
      resizable: false,
      height:180,
      modal: true,
      buttons: {
        "Login": function() {
          $( this ).dialog( "close" );
          location.href = '/accounts/login/';          
        },
        Cancel: function() {
          $( this ).dialog( "close" );
          return false;
        }
      }
    }); 
  }  
  return true;
}

function save_search(e, form_id, logged_in, receive_email) {
  if (!login_check(e, logged_in))
    return false;

    $.post('/residential/save_search/', $('#'+form_id).serialize()+'&form_id='+form_id+'&receive_email='+receive_email)
    .success(function(result){
      console.log('Search is saved successfully!');
    });
}

function profile_save_search(e) {
  receive_email = $('#userprofile-ss-propemail-0').attr('checked');
  if (receive_email != 'checked')
    receive_email = 'unchecked';
  
  save_search(e, 'rent_form', true, receive_email);
  save_search(e, 'sale_form', true);
}

function create_team()
{
    $( "#create_team_dlg" ).dialog({
      resizable: false,
      height:180,
      width:400,
      modal: true,
      buttons: {
        "Create": function() {
          var team_name = $('#team_name').val().trim();
          if(!team_name) {
            alert("Please enter the team name!");
            $('#team_name').focus();
          } else {
            $.post('/create_team', {'team_name': team_name})
            .success(function(result){
              console.log('A team is created successfully!');
              location.href = '/accounts/login/';          
              $( this ).dialog( "close" );            
            });
          }
        },
        Cancel: function() {
          $( this ).dialog( "close" );
          return false;
        }
      }
    }); 
}

function invite_member(t_id)
{
    $( "#team_member_dlg" ).dialog({
      resizable: false,
      height:180,
      width:360,
      modal: true,
      buttons: {
        "Invite": function() {
          var user_email = $('#user_email').val().trim();
          if(!user_email) {
            alert("Please enter the user's email!");
            $('#user_email').focus();
          } else {
            $.post('/invite_user', {'user_email': user_email, 't_id': t_id})
            .success(function(result){
              console.log('The user is invited successfully!');
              location.reload();          
              $( this ).dialog( "close" );            
            });
          }
        },
        Cancel: function() {
          $( this ).dialog( "close" );
          return false;
        }
      }
    }); 
}

function add_service()
{
    $( "#create_team_dlg" ).dialog({
      resizable: false,
      height:180,
      width:400,
      modal: true,
      buttons: {
        "Create": function() {
          var team_name = $('#team_name').val().trim();
          if(!team_name) {
            alert("Please enter the team name!");
            $('#team_name').focus();
          } else {
            $.post('/create_team', {'team_name': team_name})
            .success(function(result){
              console.log('A team is created successfully!');
              location.href = '/accounts/login/';          
              $( this ).dialog( "close" );            
            });
          }
        },
        Cancel: function() {
          $( this ).dialog( "close" );
          return false;
        }
      }
    }); 
}

function remove_service(s_id, t_id)
{
  var r = confirm("Are you sure to remove this service?");
  if (r == true) {
      $.post('/remove_service', {'s_id': s_id, 't_id': t_id})
      .success(function(result){
        console.log('The service is removed successfully!');
        location.reload();
      });
  } else {
      return false;
  } 
}

function cancel_account()
{
    $( "#account_cancel_dlg" ).dialog({
      resizable: false,
      height:180,
      width:400,
      modal: true,
      buttons: {
        "Confirm": function() {
          $.post('/cancel_account', {})
          .success(function(result){
            console.log('The account is canceled successfully!');
            location.reload();          
            $( this ).dialog( "close" );            
          });
        },
        Cancel: function() {
          $( this ).dialog( "close" );
          return false;
        }
      }
    }); 
}