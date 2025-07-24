import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Controls.Fusion

Dialog {
    id: createShotWindow

    property real styleColumnHeight: 32

    onAccepted: {
        shotNameInput.text = backend.get_shot_name()
        cameraInput.text = backend.get_camera_name(shotNameInput.text)
    }

    ColumnLayout {
        id: mainLayout
        anchors.fill: parent
        anchors.margins: 6

        GridLayout {
            id: inputsLayout
            Layout.alignment: Qt.AlignHCenter
            Layout.rightMargin: 12
            width: parent.width
            columns: 2
            rows: 4

            Label {
                width: createShotWindow.width/2
                Layout.alignment: Qt.AlignHCenter
                text: "Shot name:"
            }

            TextField {
                id: shotNameInput
                Layout.fillWidth: true
                Layout.rightMargin: 12
                implicitHeight: styleColumnHeight
                placeholderText: "SQ0000_SH0000"
                onEditingFinished: {
                    cameraInput.text = backend.get_camera_name(shotNameInput.text)
                }
            }

            Label {
                width: createShotWindow.width/2
                text: "Color:"
            }

            Button {
                id: colorInput
                Layout.fillWidth: true
                Layout.rightMargin: 12
                implicitHeight: styleColumnHeight
                property string selectedColor: "#ff9900ff"
                background: Rectangle {
                    radius: colorInput.radius
                    color: colorInput.selectedColor
                }
                onClicked: colorPickerPopup.open()
            }

            Label {
                width: createShotWindow.width/2
                text: "Length:"
            }

            SpinBox {
                id: shotLengthInput
                font.pixelSize:height/2
                Layout.fillWidth: true
                Layout.rightMargin: 12
                implicitHeight: styleColumnHeight
                inputMethodHints: Qt.ImhDigitsOnly
                editable: true
                from: 1
                to: 9999
                value: 24
            }

            Label {
                width: createShotWindow.width/2
                text: "Camera:"
            }

            TextField {
                id: cameraInput
                Layout.fillWidth: true
                Layout.rightMargin: 12
                implicitHeight: styleColumnHeight
                placeholderText: "CAM_SQ0000_SH0000"
            }
        }

        Button {
            Layout.alignment: Qt.AlignHCenter
            Layout.fillHeight: true
            Layout.maximumHeight: 72
            Layout.minimumWidth: 128
            leftInset: 32
            rightInset: 32
            implicitWidth: createShotWindow.width
            font.pointSize: 11
            text: "Create shot"
            onClicked: {
                backend.do_create_shot(shotNameInput.text, colorInput.selectedColor, shotLengthInput.value, cameraInput.text)
                cameraInput.selectAll()
                cameraInput.remove(cameraInput.selectionStart, cameraInput.selectionEnd)
                shotNameInput.selectAll()
                shotNameInput.remove(shotNameInput.selectionStart, shotNameInput.selectionEnd)
                createShotWindow.accept()
            }
        }

        Item {
            Layout.fillHeight: true
        }
    }
    
    Popup {
        id: colorPickerPopup
        width: 235
        height: 150
        modal: true
        focus: true
        x: (createShotWindow.width/2)-(colorPickerPopup.width/2)
        y: (createShotWindow.height/2)-(colorPickerPopup.height/2)
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        background: Rectangle {
            color: "#2a2a2a"
            radius: 8
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 8
            spacing: 10

            Label {
                Layout.alignment: Qt.AlignHCenter
                text: "Pick a color"
                color: "white"
                font.bold: true
            }

            GridLayout {
                id: colorGrid
                columns: 5
                rowSpacing: 8
                columnSpacing: 8

                Repeater {
                    
                    model: [
                        "#d32f2f",  // Muted red
                        "#f57c00",  // Deep orange
                        "#fbc02d",  // Warm yellow
                        "#8d6e63",  // Soft brown
                        "#388e3c",  // Forest green

                        "#1976d2",  // Muted blue
                        "#7b1fa2",  // Deep purple
                        "#f48fb1",  // Soft pink
                        "#4dd0e1",  // Cyan
                        "#ce93d8",  // Lavender

                        "#a1887f",  // Taupe
                        "#90caf9",  // Light blue
                        "#81c784",  // Light green
                        "#ff8a65",  // Coral
                        "#ba68c8"   // Violet
                    ]

                    delegate: Button {
                        implicitWidth: 35
                        implicitHeight: 25
                        background: Rectangle {
                            color: modelData
                            radius: 2
                            border.width: colorPickerPopup.selectedColor === modelData ? 3 : 1
                            border.color: colorPickerPopup.selectedColor === modelData ? "white" : "#555"
                        }
                        onClicked: {
                            colorInput.selectedColor = modelData
                            colorPickerPopup.close()
                        }
                    }
                }
            }
        }
    }
}
