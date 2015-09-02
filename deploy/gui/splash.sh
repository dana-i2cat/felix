#!/bin/bash

###
#   @author: CarolinaFernandez
#   @organization: i2CAT
#   @project: OFELIA FP7
#   @description: Common entry point for installation, upgrade and removal.
###

## Arguments
action_arg=$1
shift # Consume first argument
whiptail_args=$@
num_whiptail_args=$#
# Replace all "[", "]", "," by a space
whiptail_args=${whiptail_args//[\[\]\,]/ }
# Create array from list
whiptail_args=($whiptail_args)
# TODO fix and call method 'list_to_array'
#source ../utils/utils.sh
#ocf_modules=$(list_to_array "$whiptail_args")

## Paths
gui_path="./deploy/gui"

## Return code
confirm_deploy=0

## Parameters for whiptail screen
whiptail_width=45

ofver_actions=(install upgrade update remove)
case $action_arg in
    install )
        whiptail_action_title="OCF installation";
        whiptail_message_title="Installation";
        whiptail_message_description="You have stopped or cancelled the installation";
        ;;
    upgrade|update )
        whiptail_action_title="OCF upgrade";
        whiptail_message_title="Upgrade";
        whiptail_message_description="You have stopped or cancelled the upgrade";
        ;;
    remove )
        whiptail_action_title="OCF removal";
        whiptail_message_title="Removal";
        whiptail_message_description="You have stopped or cancelled the removal";
        ;;
    migrate )
        whiptail_action_title="OCF migration";
        whiptail_message_title="Migration";
        whiptail_message_description="You have stopped or cancelled the migration";
        ;;
    *)
        echo "Usage: ./splash {install | upgrade | update | remove | migrate} <modules>";
        exit 1;
        ;;
esac
whiptail_checklist_description="Choose the modules by pressing SPACE key and then TAB to reach <Ok> or <Cancel>"
whiptail_checklist_options=""


function exit_on_null_arg()
{
    if [[ $1 == "" ]]; then
        .${gui_path}/info.sh "$whiptail_message_title stopped" "$whiptail_message_description" "8" "$whiptail_width"
        confirm_deploy=1
        exit $confirm_deploy
    fi
}

function contains_element()
{
    local e
    for e in "${@:2}"; do
        [[ "$e" == "$1" ]] && echo 0 && return 0;
    done
    echo 1 && return 1
}

function do_ofver_action()
{
    for i in "${whiptail_args[@]}"
    do
        whiptail_checklist_options="$whiptail_checklist_options $i false"
    done
    
    ocf_modules_deploy=""
    while [ $confirm_deploy -eq 0 ]; do
        #./${gui_path}/checklist.sh "$whiptail_action_title" "$whiptail_checklist_description" $(($((2+$num_whiptail_args))*3)) $whiptail_width $num_whiptail_args $whiptail_checklist_options
        ocf_modules_deploy=$(whiptail --checklist --noitem "$whiptail_checklist_description" $(($(($num_whiptail_args))*3)) $whiptail_width $num_whiptail_args $whiptail_checklist_options --backtitle "OFELIA Control Framework" --title "$whiptail_action_title" 3>&1 1>&2 2>&3)
        #ocf_modules_deploy=$?
        # Saving the return code (0/1)
        exit_on_null_arg $ocf_modules_deploy
        
        ocf_modules_deploy_exitcode=$(echo $ocf_modules_deploy | rev | cut -d "\"" -f1)
        # Removing the return code
        ocf_modules_deploy=$(echo $ocf_modules_deploy | head -c -2)
        # If installation is cancelled (ocf_modules_deploy_exitcode != 0), no further step is loaded
        exit_on_null_arg $ocf_modules_deploy
        
        # Formatting the chosen OCF modules to show in a confirm box
        ocf_modules_deploy_confirmed=""
        ocf_modules_deploy_confirmed_set=($ocf_modules_deploy)
        num_ocf_modules_deploy_confirmed_set=${#ocf_modules_deploy_confirmed_set[@]}
        if [[ num_ocf_modules_deploy_confirmed_set -eq 0 ]]; then
            num_ocf_modules_deploy_confirmed_set=1
        fi
        
        for i in "${ocf_modules_deploy_confirmed_set[@]}"
        do
            # Remove quotes from module names also
            ocf_modules_deploy_confirmed="$ocf_modules_deploy_confirmed *${i//[\"]/ }\n"
        done
        
        .${gui_path}/yesno.sh "You are going to $action_arg the following modules:\n\n$ocf_modules_deploy_confirmed" $(($(($num_ocf_modules_deploy_confirmed_set+4))*2)) $whiptail_width
        confirm_deploy=$?
        # Negate exit code (whiptail --yesno => yes: 1, no: 0)
        confirm_deploy=$((! $confirm_deploy ))
    done
    # Write file to be parsed later
    echo $ocf_modules_deploy > ocf_modules_deploy
}

function do_migration()
{
    chosen_folder=$(dirname $PWD)
    while [ $confirm_deploy -eq 0 ]; do
        ocf_modules_deploy=$(whiptail --inputbox "Please choose the destination path for your code" 8 78 $chosen_folder --title "$whiptail_action_title" --backtitle "OFELIA Control Framework" 3>&1 1>&2 2>&3)
        # Update chosen folder to the last value set by the user
        chosen_folder=$ocf_modules_deploy
        # Saving the return code (0/1)
        exit_on_null_arg $chosen_folder

        .${gui_path}/yesno.sh "You are about to $action_arg the OCF modules to the following location:\n\n$ocf_modules_deploy" $(($((1+4))*2)) $whiptail_width
        confirm_deploy=$?
        # Negate exit code (whiptail --yesno => yes: 1, no: 0)
        confirm_deploy=$((! $confirm_deploy ))
    done
    # Write file to be parsed later
    echo $ocf_modules_deploy > ocf_modules_deploy
}

function main()
{
    if [[ $(contains_element "$action_arg" "${ofver_actions[@]}") == 0 ]]; then
        do_ofver_action $@
    elif [[ $action_arg == "migrate" ]]; then
        do_migration $@
    fi
}

main $@
return_code=$?
exit $return_code
