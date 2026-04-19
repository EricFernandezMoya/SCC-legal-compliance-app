# THIS IS JUST A SCRATCH CODE TO LEARN HOW TKINTER WORKS

from tkinter import *
from tkinter.ttk import *
from anthropicConnection import textQueryToAntropic
from insertDocWindows import getFrame



class FrameSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("SCC Legal Compliance Software")
        self.root.geometry("1000x1000")
        
        # Create container frame
        self.container = Frame(root)
        self.container.pack(side=TOP, fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        # Create frames dictionary
        self.frames = {}
        
        # Create different frames
        for frame_class in (HomePage, SettingsPage):
            frame = frame_class(self.container, self)
            self.frames[frame_class] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        # Show initial frame
        self.show_frame(HomePage)
    
    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        frame.tkraise()

class HomePage(Frame):
    
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        label = Label(self, text="Home Page", font=("Arial", 16))
        label.pack(pady=20)
        
        buttonSettingPage = Button(
            self,
            text="Go to Settings",
            command=lambda: controller.show_frame(SettingsPage)
        )
        buttonSettingPage.pack(pady=20)

        # IMPORTANT: must use self.insertDocWindows
        buttonInsertLegalDocument = Button(
            self,
            text="Insert Doc",
            command= lambda: self.insertDocWindows(self)
        )
        buttonInsertLegalDocument.pack(pady=20)

    def insertDocWindows(self):
                
        new_window = Toplevel(self.controller.root)
        new_window.title("Insert Legal Document")
        new_window.geometry("500x500")

        if new_window.title == "Insert Legal Document":

            Label(new_window, text="Insert Legal Document", font=("Arial", 16)).place(x=10, y=10)

            Label(new_window, text="Document name:").place(x=10, y=100)
            Text(new_window, width=50, height=1).place(x=10, y=120)

            Label(new_window, text="Jurisdiction:").place(x=10, y=150)
            Text(new_window, width=50, height=1).place(x=10, y=170)

            Label(new_window, text="Description:").place(x=10, y=200)
            Text(new_window, width=50, height=15).place(x=10, y=220)

class SettingsPage(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        labelTop = Label(self, text="Anthropic Conection", font=("Arial", 16))
        labelTop.pack(pady=20)

        labelAskQuestion = Label(self, text="Ask a question to the AI")
        labelAskQuestion.pack(pady=20)

        questionText = Text(self,  height=15, width=100, bg="light blue")
        questionText.pack(pady=20, padx=20)

        searchButton = Button(self, width = 20, text ="Search", command = lambda: queryAI())
        searchButton.pack()

        answerText = Text(self,height=15, width=100, bg="light blue")
        answerText.pack(pady=20, padx=20)
        
        button = Button(self, text="Go to Home", command=lambda: controller.show_frame(HomePage))
        button.pack()

        def queryAI():
            textInput = questionText.get("1.0", "end-1c")
            textOutput = textQueryToAntropic(textInput)
            answerText.insert(END, textOutput)


# Create and run application
root = Tk()
app = FrameSwitcher(root)
root.mainloop()