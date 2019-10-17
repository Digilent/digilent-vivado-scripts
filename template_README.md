Arty-Z7-20-hdmi-in demo
====================

Description
-----------

The first paragraph of this section describes what peripherals of the board are used, and what the demo does, at a high level.

Later paragraphs of this section can go into more detail, describing specific features of the demo, such as what messages can be printed by the demo, what options the user can configure, and important additional requirements.

Requirements
------------
* This section contains a bulleted list of hardware and software requirements.
* Typically, this includes the board, with a link to the store page.
* Development environments and other required software, with links to installation guides.
* And any other cables and hardware (HDMI cables and monitors for example) that are required.

Demo Setup
----------

*This section is a step by step guide from downloading the release to programming the board and running the demo. All caps text in "< >" brackets is intended to be replaced in the final README.*

1. Download the most recent release ZIP archive ("\<DEMO\>-\<VERSION\>-*.zip") from the repo's [releases page](https://github.com/Digilent/\<DEMO\>/releases).

2. Extract the downloaded ZIP.

3. Open the XPR project file, found at \<archive extracted location\>/vivado_proj/\<DEMO\>.xpr, included in the extracted release archive in Vivado \<VERSION\>.

*Some demos only use Vivado, and not Xilinx SDK. In this case, use the following version of steps 4 to end:*

4. In the Flow Navigator panel on the left side of the Vivado window, click **Open Hardware Manager**.

5. Plug the \<BOARD\> into the computer using a MicroUSB cable via it's \<PORT LABEL\> programming port.

*Do not include step 6 if the demo doesn't use UART.*

6. Open a serial terminal emulator (such as TeraTerm) and connect it to the Basys 3's serial port, using a baud rate of \<BAUD\>.

7. In the green bar at the top of the Vivado window, click **Open target**. Select **Auto connect** from the drop down menu.

8. In the green bar at the top of the Vivado window, click **Program device**.

9. In the Program Device Wizard, enter "\<archive extracted location\>/vivado_proj/\<DEMO\>.runs/impl_1/\<FILENAME\>.bit" into the "Bitstream file" field. Then click **Program**.

10. The demo will now be programmed onto the \<BOARD\>. See the *Description* section of this README to learn how to interact with this demo.

*For demos that use SDK, use the following version of steps 4 to end:*

4. Launch Xilinx SDK directly (not through the Vivado file menu). When prompted for a workspace, select "\<archive extracted location\>/sdk_workspace".
5. Once the workspace opens, click the **Import** button. In the resulting dialog, first select *Existing Projects into Workspace*, then click **Next**. Navigate to and select the same sdk_workspace folder.
6. Build the project. **Note**: *Errors are sometimes seen at this step. These are typically resolved by right-clicking on the BSP project and selecting Regenerate BSP Sources.*

*Here is where hardware setup should be described, for example:*

7. Plug in the HDMI IN/OUT cables as well as the HDMI capable Monitor/TV.

8. Open a serial terminal application (such as [TeraTerm](https://ttssh2.osdn.jp/index.html.en) and connect it to the \<BOARD\>'s serial port, using a baud rate of \<BAUD\>.

9. In the toolbar at the top of the SDK window, select *Xilinx -> Program FPGA*. Leave all fields as their defaults and click "Program".

10. In the Project Explorer pane, right click on the "\<APP NAME\>" application project and select "Run As -> Launch on Hardware (System Debugger)".

11. The application will now be running on the \<BOARD\>. It can be interacted with as described in the first section of this README.

12. Lastly, the hardware platform must be linked to a hardware handoff, so that changes to the Vivado design can be brought into the SDK workspace. In Vivado, in the toolbar at the top of the window, select *File -> Export -> Export Hardware*. Any Exported Location will do, but make sure to remember the selection, and make sure that the **Include bitstream** box is checked. Click **OK**.

13. In SDK, right click on the \*_hw_platform_\* project, and select *Change Hardware Platform Specification*. Click **Yes** in response to the warning. In the resulting dialog, navigate to and select the .hdf hardware handoff file exported in the previous step, then click **OK**. Now, whenever a modified design is exported from Vivado, on top of the .hdf file, it can be applied to the hardware platform.

Next Steps
----------
*This section is primarily used to link to useful resources*

This demo can be used as a basis for other projects by modifying the hardware platform in the Vivado project's block design or by modifying the SDK application project.

Check out the Arty Z7-20's [Resource Center](https://reference.digilentinc.com/reference/programmable-logic/arty-z7/start) to find more documentation, demos, and tutorials.

For technical support or questions, please post on the [Digilent Forum](forum.digilentinc.com).

Additional Notes
----------------
For more information on how this project is version controlled, refer to the [digilent-vivado-scripts repo](https://github.com/digilent/digilent-vivado-scripts).