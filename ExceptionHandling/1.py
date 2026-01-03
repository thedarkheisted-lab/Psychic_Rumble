#       Example 1

# try:
#     even_numbers = [2,4,6,8]
#     print(even_numbers[5])

# except ZeroDivisionError:
#     print("Denominator cannot be 0")

# except IndexError:
#     print("Index out of bounds")


#       Example 2

# try:
#     num = int(input("Enter a number: "))
#     assert num % 2 == 0
# except:
#     print("Not an Even number")
# else:
#     reciprocal = 1/num
#     print(reciprocal)

#       Example 3

try:
    numerator  = int(input("Enter num: "))
    denominator = int(input("Enter the denom: "))

    result = numerator/denominator

    print(result)

except:
    print("Error: Denominator can't be zero")

finally:
    print("You stupid fuck")