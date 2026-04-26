from claudeConnection import textQueryToAntropic
import tkinter as tk
from tkinter import Frame, Label, Button, Toplevel, Text, PhotoImage, filedialog, Entry, StringVar, OptionMenu
from tkcalendar import DateEntry
from userHandling import *
from database import *
from classesFile import User

ERROR_SIZE = "250x80"
LOGIN_FRAME_SIZE = "300x300"
MEDIUM_FRAME_SIZE = "500x500"
LARGE_FRAME_SIZE = "1000x1000"

user = User("", "", "", "")

def show_frame(frame, frameSize):
    root.geometry(frameSize)
    frame.tkraise()

root = tk.Tk()

root.title("SCC Legal")

# Setup layout to make frames fill the space
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)

logInFrame = Frame(root)
mainFrame = Frame(root)
anthropicFrame = Frame(root)

for frame in (logInFrame, mainFrame, anthropicFrame ):
    frame.grid(row=0, column=0, sticky='nsew')

# show_frame(logInFrame, LOGIN_FRAME_SIZE)
show_frame(anthropicFrame, LARGE_FRAME_SIZE)


#################################################################################
#                                                                               #
#                                  LOGIN FRAME                                  #
#                                                                               #
#################################################################################
def login():
    
    username = usernameText.get("1.0", "end-1c")
    password = passwordEntry.get()
    
    if userLogin(username, password):
        
        user = selectUser(username)
        
        userLabel.config(text=username)
        
        show_frame(mainFrame, MEDIUM_FRAME_SIZE)

    else:

        new_window = Toplevel(root)
        new_window.title("Error")
        new_window.geometry(ERROR_SIZE)
    
        titleLabel = Label(new_window, text="Wrong user name or password", fg="red")
        titleLabel.place( relx= 0.5, rely= 0.5, anchor= 'center')

    usernameText.delete("1.0", "end")
    passwordEntry.delete(0, "end")

loginTitleLabel = Label(logInFrame, text="Login", font=("Arial", 16))
loginTitleLabel.place(relx=0.5, y=20, anchor='center')

usernameLabel =Label(logInFrame, text="User name:")
usernameLabel.place(x=10, y=50)
usernameText = Text(logInFrame, width=25, height=1)
usernameText.place(x=10, y=70)

passwordLabel = Label(logInFrame, text="Password:")
passwordLabel.place(x=10, y=110)
passwordEntry = Entry(logInFrame, width=25, show="*")
passwordEntry.place(x=10, y=130)
passwordEntry.bind("<Return>", lambda event: login())

loginButton = Button(logInFrame, text="Log in", command= lambda:login())
loginButton.place(x=10, y=170)

#################################################################################
#                                                                               #
#                                   MAIN FRAME                                  #
#                                                                               #
#################################################################################


homePageTitlelabel = Label(mainFrame, text="Home Page", font=("Arial", 16))
homePageTitlelabel.place(relx=0.5, y=20, anchor='center')

userLabel = Label(mainFrame)
userLabel.place(x=10, y=10)

buttonSettingPage = Button(mainFrame, text="Go to AI Query", command= lambda: show_frame(anthropicFrame, LARGE_FRAME_SIZE))
buttonSettingPage.place(relx=0.5, y=120, anchor='center')
        
buttonInsertLegalDocument = Button(mainFrame, text="Insert Doc", command= lambda: insertDocWindows())
buttonInsertLegalDocument.place(relx=0.5, y=170, anchor='center')

buttonUpdateLegalDocument = Button(mainFrame, text="Update Doc", command= lambda: updateDocWindows())
buttonUpdateLegalDocument.place(relx=0.5, y=220, anchor='center')

logoutButton = Button(mainFrame, text="Log out", command= lambda: show_frame(logInFrame, LOGIN_FRAME_SIZE))
logoutButton.place(relx=0.5, y=270, anchor='center')


#################################################################################
#                                                                               #
#                                ANTHROPIC FRAME                                #
#                                                                               #
#################################################################################

labelTop = Label(anthropicFrame, text="Anthropic Conection", font=("Arial", 16))
labelTop.place(relx=0.5, y=20, anchor='center')

labelAskQuestion = Label(anthropicFrame, text="Ask a question to Anthropic:")
labelAskQuestion.place(x=100, y=80)

questionText = Text(anthropicFrame,  height=15, width=100, bg="light blue")
questionText.place(relx=0.5, y=110, anchor='n')

searchButton = Button(anthropicFrame, width = 20, text ="Search", command = lambda: queryAI())
searchButton.place(relx=0.5, y=390, anchor='n')

answerText = Text(anthropicFrame,height=15, width=100, bg="light blue")
answerText.place(relx=0.5, y=450, anchor='n')
        
button = Button(anthropicFrame, text="Go to Home", command=lambda: show_frame(mainFrame, MEDIUM_FRAME_SIZE))
button.place(relx=0.5, y=730, anchor='n')

def queryAI():
    textInput = questionText.get("1.0", "end-1c")
    textOutput = textQueryToAntropic(textInput)
    answerText.insert(tk.END, str(textOutput))


def insertDocWindows():
                
    new_window = Toplevel(root)
    new_window.title("Insert Legal Document")
    new_window.geometry(MEDIUM_FRAME_SIZE)

    
    titleLabel = Label(new_window, text="Insert Legal Document", font=("Arial", 16))
    titleLabel.place(x=10, y=10)

    nameLabel =Label(new_window, text="Document name:")
    nameLabel.place(x=10, y=100)
    nameText = Text(new_window, width=50, height=1)
    nameText.place(x=10, y=120)

    jurisdictionLabel = Label(new_window, text="Jurisdiction:")
    jurisdictionLabel.place(x=10, y=150)
    jurisdictionText = Text(new_window, width=50, height=1)
    jurisdictionText.place(x=10, y=170)

    descriptionLabel = Label(new_window, text="Description:")
    descriptionLabel.place(x=10, y=200)
    descriptionText = Text(new_window, width=50, height=15)
    descriptionText.place(x=10, y=220)

def selectFilePath(filePathText, parent_window):
    types = [("Data Files", "*.pdf *.doc *.docx *.odt"), ("All Files", "*.*")]
    filePath = filedialog.askopenfilename(title="Select a File", filetypes=types)
    
    parent_window.deiconify()
    parent_window.lift()
    parent_window.focus_force()
    
    if filePath:
        filePathText.delete("1.0", "end")
        filePathText.insert("1.0", filePath)

def updateDocWindows():
    
    new_window = Toplevel(root)
    new_window.title("Insert Legal Document")
    new_window.geometry(MEDIUM_FRAME_SIZE)
    new_window.transient(root)
    new_window.grab_set()
    new_window.focus_force()

    versionLabel = Label(new_window, text="Version:")
    versionLabel.place(x=10, y=100)
    versionText = Text(new_window, width=50, height=1)
    versionText.place(x=10, y=120)

    effectiveFromLabel = Label(new_window, text="Effective from:")
    effectiveFromLabel.place(x=10, y=150)
    effectiveFromDateEntry = DateEntry(new_window, width=10, background='darkblue', foreground='white', borderwidth=2)
    effectiveFromDateEntry.place(x=10, y=170)

    effectiveToLabel = Label(new_window, text="Effective to:")
    effectiveToLabel.place(x=150, y=150)
    effectiveToDateEntry = DateEntry(new_window, width=10, background='darkblue', foreground='white', borderwidth=2)
    effectiveToDateEntry.place(x=150, y=170)

    sourceUrlLabel = Label(new_window, text="Source url:")
    sourceUrlLabel.place(x=10, y=200)
    sourceUrlText = Text(new_window, width=50, height=1)
    sourceUrlText.place(x=10, y=220)

    filePathLabel = Label(new_window, text="File path:")
    filePathLabel.place(x=10, y=250)
    filePathText = Text(new_window, width=50, height=1)
    filePathText.place(x=10, y=270)
    filePathIcon = PhotoImage(file="searchFileIcon.png").subsample(8, 8)

    filePathButton = Button(new_window, image=filePathIcon, command=lambda: selectFilePath(filePathText, new_window), padx=5, pady=5)
    filePathButton.image = filePathIcon  # prevent garbage collection
    filePathButton.place(x=430, y=270)
    
    notesLabel = Label(new_window, text="Description:")
    notesLabel.place(x=10, y=300)
    notesText = Text(new_window, width=50, height=5)
    notesText.place(x=10, y=320)


root.mainloop()
