# Begin looper bash autocomplete
_looper_autocomplete()
{
    local cur prev opts1 opts2
    cur=${COMP_WORDS[COMP_CWORD]}
    prev=${COMP_WORDS[COMP_CWORD-1]}
    opts1=$(looper --commands)
#    opts2=$(looper list --simple)
    case ${COMP_CWORD} in
        1)
            COMPREPLY=($(compgen -W "${opts1}" -- ${cur}))
            ;;
        2)
#            case ${prev} in
#                "activate"|"run")
#                    COMPREPLY=($(compgen -W "${opts2}" -- ${cur}))
#                    ;;
#                *)
#                    COMPREPLY=()
#                    ;;
#            esac
#            ;;
#        *)
            COMPREPLY=()
            ;;
    esac
} && complete -o bashdefault -o default -F _looper_autocomplete looper
# end looper bash autocomplete