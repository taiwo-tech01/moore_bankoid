from decimal import Decimal
from django.shortcuts import render,redirect
from django.http import HttpResponse, HttpRequest, JsonResponse
from .models import Transaction, Profile, Account, KYCDocument 
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q

# Create your views here.
def loginView(request : HttpRequest) :
    error ,message =None,None
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        if not password or len(password) < 8 :
            return render(request,'login.html',{"error":True, "message":"password is requiredand must meet minimum to login"})
        User_returned = authenticate(request, username=email, password=password)
        if not User_returned :
            return render(request, 'login.html', {error:True, "message":"Invaild Credentails"})
        login(request, User_returned)
        return redirect("client_dashboard")
    
    return render(request, 'login.html', {"error":error, "message":message})

    # return HttpResponse('''
    #   <a href="http://127.0.0.1:5500/Gidex/BOA.html">come here</a>
    #     <h2>Logins</h2>
    #     <p>LOGIN PAGE FORM</p>
    #     '''
    
def signUp(request : HttpRequest) :
    error = None
    if request.method == "POST":
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2 or len(password1) < 8 :
            error = 'ensure both passwords match and length is greater than 7'
        else : 
            try :
                user_exist = User.objects.filter(username = email).first()
                if user_exist :
                    error = 'User already exists for this account'
                else:
                    user = User.objects.create_user(username=email, password=password1)
                    # we can generate account for that user
                    account = Account.objects.create(user = user)
                    user.save()
                    account.save()
                    return redirect("client_login")
            except Exception as e :
                error = str (e)
    return render(request, 'signup.html', {"error" : error})

@login_required(login_url='client_login')
def transferPage(request: HttpRequest):
    error = None
    owner_account = Account.objects.get(user=request.user)
    if request.method == "POST":
        reciever_account_number = request.POST.get("account_number")
        amount_to_send = request.POST.get("amount")
        sender_pin = request.POST.get("pin")

        # frist check amount is valid then check if the balance is enough 
        if not amount_to_send or not amount_to_send.isdigit():
            return render(request, "transfer.html",{"error":"Amount to send must be a valid number","account":owner_account})
        
        user_balance = owner_account.balance
        amount_in_decimal = Decimal(amount_to_send)
        # user balance must not be less than amount he or she is to send
        if user_balance < amount_in_decimal :
             return render(request, 'transfer.html', {'error': 'Bobo u  no get money!!!','account':owner_account})

       # check  if the user send in the pin 
        if not sender_pin or not sender_pin.isdigit() or len(sender_pin) != 4:
          return render(request, 'transfer.html', {'error':"You must enter your pin and must be a 4 digit pin",'account':owner_account})
       # Next confirm the user pin
        is_pin_correct = owner_account.verifyPass(sender_pin)
        if not is_pin_correct :
             return render(request, 'transfer.html', {'error':'Invaild pin entered','account':owner_account})
       # Next is for checking the account of the reciever etc
        if not reciever_account_number or not reciever_account_number.isdigit() or len (reciever_account_number) != 10 :
            return render(request, 'transfer.html', {'error':'Reciever Account number must exist and must be a 10 digit number!','account':owner_account}) 
        
        try :
            reciever_account = Account.objects.get(account_number = reciever_account_number)
            # increase the reciever balance and decrease the sender balance
            reciever_account.balance += amount_in_decimal
            owner_account.balance -= amount_in_decimal

            owner_account.save()
            reciever_account.save()

            # document the transfer into transaction model ....
            transaction = Transaction.objects.create(from_account = owner_account, to_account = reciever_account, amount = amount_in_decimal, status = 'success', transaction_type = 'transfer')
            transaction.save()
            # here u redirect instead of going to the same page ....
            return render(request, 'transfer.html', {"success": f"Transfer of NGN {amount_to_send} Money sent succesfully to {reciever_account.user.username}",'account': owner_account, 'transaction_ref': transaction.ref})
        
        except Account.DoesNotExist:
            return render(request, 'transfer.html', {'error':f'Account Number {reciever_account_number} not found!','account':owner_account})

    return render(request, 'transfer.html', {'error': error,'account':owner_account})

@login_required(login_url='client_login')
def pinPage(request: HttpRequest):
    user_has_pin = False
    account = Account.objects.get(user =request.user)
    if account.pin_hash:
        user_has_pin = True

    if request.method == "POST":
        new_pin = request.POST.get("new_pin")
        confirm_pin = request.POST.get("confirm_pin")

        if not new_pin or new_pin != confirm_pin or len(new_pin) != 4 or not new_pin.isdigit():
             return render(request,'pin.html', {'user_has_pin': user_has_pin, "error":'pin must be digit and length must not be less than 4'})    
        
        if user_has_pin:
            current_pin = request.POST.get("current_pin")
            if not current_pin or len(new_pin) != 4 or not current_pin.isdigit():
             return render(request,'pin.html', {'user_has_pin': user_has_pin, "error":'you must enter your current pin and it must be a 4 digit pin'})
            # now we verify the old password if it matches the one stored in our hash
            is_correct = account.verifyPass(current_pin)
            if not is_correct:
                return render(request,'pin.html',{"user_has_pin":user_has_pin,"error":"Wrong pin entered"})
            account.createpin(new_pin)
            return render(request,'pin.html',{"user_has_pin": True,"success":"Pin updated succesfully"})

            # if we doing update we process them all in there  
        
        # if it gets down here this means this user have not set a password before
        # at this stage it means all validation for setting a new password
        account.createpin(new_pin)
        return render(request, 'pin.html', {"user_has_pin": True,'success':"Pin created successfully"})

    return render(request, 'pin.html', {'user_has_pin': user_has_pin})

@login_required(login_url='client_login')
def profilePage(request: HttpRequest):
    return render(request, 'profile.html', {})

@login_required(login_url='client_login')
def dashboardPage(request: HttpRequest):
    user = request.user
    account = Account.objects.get(user=user)
    return render(request, 'dashboard.html', {"account":account})


@login_required(login_url='client_login')
def TransactionPage(request:HttpRequest):
    account =Account.objects.get(user=request.user)
    transactions = Transaction.objects.filter(Q(from_account = account) | Q(to_account= account) )
    return render(request, 'Transactions.html',{'transactions': transactions})


@login_required(login_url='client_login')
def searchUser(request:HttpRequest):
    user_to_search = request.GET.get('search')
    if not user_to_search :
        return HttpResponse('<p>Nothin to search </p>')
    try:
        user_found = User.objects.get(username = user_to_search )
        return HttpResponse(f"<p>User{user_found.username} found with id {user_found.id} ")
    except User.DoesNotExist as e :
        return HttpResponse('<P>user does not  exist </P> ')
    except Exception as e :
        return HttpResponse("Error occurred")

@login_required(login_url='client_login')
def logout_page(request:HttpRequest):
    logout(request)
    return redirect('client_login')


# def cardPurchaseEndpoint(request) :
#     description = {
#         "buy card" : "/card/purchase",
#         "amount" : [500,1000,2000,5000],
#         "method" : "POST"
#     }
#     return JsonResponse(
#         data = description
#     )
# def getAllProfile(request: HttpRequest) -> JsonResponse:
#     profiles = Profile.objects.filter()
#     data = {}
#     count = 0
#     for profile in profiles:
#         data[count] = {
#             "username" : profile.user.username,
#             "phone" : profile.phone
#         }
#         count +=1

#     return JsonResponse(
#         data= data,
#         safe = False
#     )

# @login_required(login_url='client_login')
# def profilePage(request, profile_id : int):
#     try:
#         user_profile = Profile.objects.get(id=profile_id)
#     except Profile.DoesNotExist :
#         return  render(request, 'profiles.html', {"username":None})
#     return render(request, 'profiles.html',{"username": user_profile.user.username})

