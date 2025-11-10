import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Controls.Fusion

Page {
    id: sequencerWindow
    anchors.fill: parent

    palette {
        window: "#313131"              // Main background (softer than pure black)
        windowText: "#f0f0f0"          // Default text
        base: "#1f1f1f"                // Background for text inputs, etc.
        alternateBase: "#323232"       // Alternate row backgrounds
        text: "#ffffff"                // Text inside controls
        button: "#444444"              // Button background
        buttonText: "#ffffff"          // Button text
        brightText: "#ffffff"          // For highlighted text
        highlight: "#0078d7"           // Selection highlight (e.g., list items)
        highlightedText: "#ffffff"     // Text on highlighted background
        light: "#4a4a4a"               // Light border/shadow
        midlight: "#3e3e3e"            // Slightly lighter than base
        dark: "#2a2a2a"                // Darker than base
        mid: "#363636"                 // Mid-tone
        shadow: "#1a1a1a"              // Shadow color
        placeholderText: "#7c7c7c"     // Placeholder text in inputs
    }

    property real buttonsSize: 48

    RowLayout {
        anchors.fill: parent
        anchors.margins: 6
        
        GridLayout {
            columns: 6
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignLeft
            Layout.maximumWidth: 100
        
            Button {
                id: createShotBtn
                Layout.fillHeight: true
                Layout.alignment: Qt.AlignLeft | Qt.AlignTop
                Layout.maximumHeight: buttonsSize
                Layout.maximumWidth: buttonsSize
                contentItem: Image {
                    source: "icons/plus.svg"
                    fillMode: Image.PreserveAspectFit
                    anchors.fill: parent
                    anchors.margins: 6
                }
                ToolTip.visible: hovered
                ToolTip.text: "Create Shot"
                onClicked: {
                    backend.open_create_shot_dialog()
                }
            }

            Button {
                id: deleteShotBtn
                Layout.fillHeight: true
                Layout.alignment: Qt.AlignLeft | Qt.AlignTop
                Layout.maximumHeight: buttonsSize
                Layout.maximumWidth: buttonsSize
                contentItem: Image {
                    source: "icons/trash.svg"
                    fillMode: Image.PreserveAspectFit
                    anchors.fill: parent
                    anchors.margins: 6
                }
                ToolTip.visible: hovered
                ToolTip.text: "Delete shot"
                onClicked: backend.delete_shot()
            }

            Button {
                id: focusBtn
                Layout.fillHeight: true
                Layout.alignment: Qt.AlignLeft | Qt.AlignTop
                Layout.maximumHeight: buttonsSize
                Layout.maximumWidth: buttonsSize
                contentItem: Image {
                    source: "icons/zoomin.svg"
                    fillMode: Image.PreserveAspectFit
                    anchors.fill: parent
                    anchors.margins: 6
                }
                ToolTip.visible: hovered
                ToolTip.text: "Focus active shot"
                onClicked: backend.focus_active_shot()
            }

            Button {
                id: defocusBtn
                Layout.fillHeight: true
                Layout.alignment: Qt.AlignLeft | Qt.AlignTop
                Layout.maximumHeight: buttonsSize
                Layout.maximumWidth: buttonsSize
                contentItem: Image {
                    source: "icons/zoomout.svg"
                    fillMode: Image.PreserveAspectFit
                    anchors.fill: parent
                    anchors.margins: 6
                }
                ToolTip.visible: hovered
                ToolTip.text: "Defocus"
                onClicked: backend.defocus_active_shot()
            }

            Button {
                id: previousBtn
                Layout.fillHeight: true
                Layout.alignment: Qt.AlignLeft | Qt.AlignTop
                Layout.maximumHeight: buttonsSize
                Layout.maximumWidth: buttonsSize
                contentItem: Image {
                    source: "icons/arrowleft.svg"
                    fillMode: Image.PreserveAspectFit
                    anchors.fill: parent
                    anchors.margins: 6
                }
                ToolTip.visible: hovered
                ToolTip.text: "Focus previous shot"
                onClicked: backend.focus_previous_shot()
            }

            Button {
                id: nextBtn
                Layout.fillHeight: true
                Layout.alignment: Qt.AlignLeft | Qt.AlignTop
                Layout.maximumHeight: buttonsSize
                Layout.maximumWidth: buttonsSize
                contentItem: Image {
                    source: "icons/arrowright.svg"
                    fillMode: Image.PreserveAspectFit
                    anchors.fill: parent
                    anchors.margins: 6
                }
                ToolTip.visible: hovered
                ToolTip.text: "Focus next shot"
                onClicked: backend.focus_next_shot()
            }

            Button {
                id: removeFrameBtn
                Layout.fillHeight: true
                Layout.alignment: Qt.AlignLeft | Qt.AlignTop
                Layout.maximumHeight: buttonsSize
                Layout.maximumWidth: buttonsSize
                contentItem: Image {
                    source: "icons/arrowremove.svg"
                    fillMode: Image.PreserveAspectFit
                    anchors.fill: parent
                    anchors.margins: 6
                }
                ToolTip.visible: hovered
                ToolTip.text: "Reduce shot length"
                onClicked: backend.reduce_active_shot_length()
            }

            Button {
                id: addFrameBtn
                Layout.fillHeight: true
                Layout.alignment: Qt.AlignLeft | Qt.AlignTop
                Layout.maximumHeight: buttonsSize
                Layout.maximumWidth: buttonsSize
                contentItem: Image {
                    source: "icons/arrowadd.svg"
                    fillMode: Image.PreserveAspectFit
                    anchors.fill: parent
                    anchors.margins: 6
                }
                ToolTip.visible: hovered
                ToolTip.text: "Increase shot length"
                onClicked: backend.increase_active_shot_length()
            }

            Button {
                id: linkShotsBtn
                Layout.fillHeight: true
                Layout.alignment: Qt.AlignLeft | Qt.AlignTop
                Layout.maximumHeight: buttonsSize
                Layout.maximumWidth: buttonsSize
                contentItem: Image {
                    source: "icons/link.svg"
                    fillMode: Image.PreserveAspectFit
                    anchors.fill: parent
                    anchors.margins: 6
                }
                ToolTip.visible: hovered
                ToolTip.text: "Fill gaps"
                onClicked: backend.link_shots()
            }

            Button {
                id: unlinkShotsBtn
                Layout.fillHeight: true
                Layout.alignment: Qt.AlignLeft | Qt.AlignTop
                Layout.maximumHeight: buttonsSize
                Layout.maximumWidth: buttonsSize
                contentItem: Image {
                    source: "icons/unlink.svg"
                    fillMode: Image.PreserveAspectFit
                    anchors.fill: parent
                    anchors.margins: 6
                }
                ToolTip.visible: hovered
                ToolTip.text: "Unstack shots"
                onClicked: backend.unstack_shots()
            }

            Button {
                id: playblastBtn
                Layout.fillHeight: true
                Layout.alignment: Qt.AlignLeft | Qt.AlignTop
                Layout.maximumHeight: buttonsSize
                Layout.maximumWidth: buttonsSize
                contentItem: Image {
                    source: "icons/play.svg"
                    fillMode: Image.PreserveAspectFit
                    anchors.fill: parent
                    anchors.margins: 6
                }
                ToolTip.visible: hovered
                ToolTip.text: "Quickblast"
                onClicked: backend.playblast()
            }

            Button {
                id: exportBtn
                Layout.fillHeight: true
                Layout.alignment: Qt.AlignLeft | Qt.AlignTop
                Layout.maximumHeight: buttonsSize
                Layout.maximumWidth: buttonsSize
                contentItem: Image {
                    source: "icons/export.svg"
                    fillMode: Image.PreserveAspectFit
                    anchors.fill: parent
                    anchors.margins: 6
                }
                ToolTip.visible: hovered
                ToolTip.text: "Export sequence datas"
                onClicked: backend.export_sequence_datas()
            }

            Item {
                id: fillerVertical
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignLeft
                implicitWidth: 1
            }
        }
        Item {
            id: fillerHorizontal
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignLeft
        }
    }
}