module calculate_module
    use utils_module, only: dp
    implicit none
    contains

    subroutine calculate_point(loglikelihood,prior,point,settings,nlike)
        use settings_module, only: program_settings
        implicit none
        interface
            function loglikelihood(theta,phi)
                import :: dp
                real(dp), intent(in),   dimension(:) :: theta
                real(dp), intent(out),  dimension(:) :: phi
                real(dp) :: loglikelihood
            end function
        end interface
        interface
            function prior(cube) result(theta)
                import :: dp
                real(dp), intent(in), dimension(:) :: cube
                real(dp), dimension(size(cube))    :: theta
            end function
        end interface

        type(program_settings), intent(in) :: settings
        real(dp), intent(inout) , dimension(:) :: point
        integer, intent(inout) :: nlike

        real(dp),dimension(settings%nDims)    :: cube   ! Hypercube coordinate
        real(dp),dimension(settings%nDims)    :: theta  ! Physical parameters
        real(dp),dimension(settings%nDims)    :: mn, mx ! Min and max bounds
        real(dp),dimension(settings%nDerived) :: phi    ! derived parameters
        real(dp)                              :: logL
        
        mn = merge(-1d0,0d0,settings%wraparound)
        mx = merge(2d0,1d0,settings%wraparound)

        cube = point(settings%h0:settings%h1)

        if ( any(cube<mn) .or. any(cube>mx) )  then
            theta = 0
            logL  = settings%logzero
        else
            where(settings%wraparound) cube = modulo(cube,1d0)
            theta = prior(cube)
            logL  = loglikelihood(theta,phi)
        end if

        if(logL>settings%logzero) nlike = nlike+1

        point(settings%h0:settings%h1) = cube
        point(settings%p0:settings%p1) = theta
        point(settings%d0:settings%d1) = phi
        point(settings%l0) = logL

    end subroutine calculate_point

    !> Calculate a posterior point from a live/phantom point
    function calculate_posterior_point(settings,point,logweight,evidence,volume) result(posterior_point)
        use settings_module,   only: program_settings
        use utils_module,      only: logincexp
        implicit none

        type(program_settings), intent(in) :: settings
        real(dp), dimension(settings%nTotal),intent(in) :: point
        real(dp),intent(in) :: logweight
        real(dp),intent(in) :: evidence
        real(dp),intent(in) :: volume
        real(dp), dimension(settings%nposterior) :: posterior_point


        ! Volume
        posterior_point(settings%pos_X)  = volume
        ! Likelihood
        posterior_point(settings%pos_l)  = point(settings%l0)
        ! Un-normalised weighting 
        posterior_point(settings%pos_w)  = logweight
        ! un-normalise cumulative weighting
        posterior_point(settings%pos_Z)  = evidence
        ! Physical parameters
        posterior_point(settings%pos_p0:settings%pos_p1) = point(settings%p0:settings%p1)
        ! Derived parameters
        posterior_point(settings%pos_d0:settings%pos_d1) = point(settings%d0:settings%d1)

    end function calculate_posterior_point


    !> This function computes the similarity matrix of an array of data.
    !!
    !! Assume that the data_array can be considered an indexed array of vectors
    !! V = ( v_i : i=1,n )
    !!
    !! The similarity matrix can be expressed very neatly as
    !! d_ij = (v_i-v_j) . (v_i-v_j)
    !!      = v_i.v_i + v_j.v_j - 2 v_i.v_j
    !!
    !! The final term can be written as a data_array^T data_array, and the first
    !! two are easy to write. We can therefore calculate this in two lines with
    !! instrisic functions
    function calculate_similarity_matrix(data_array, wraparound) result(similarity_matrix)

        real(dp), intent(in), dimension(:,:) :: data_array
        logical, intent(in), dimension(size(data_array,1)) :: wraparound

        real(dp), dimension(size(data_array,2),size(data_array,2)) :: similarity_matrix
        real(dp), dimension(size(data_array,1)) :: v

        integer :: i, j
        do i=1, size(data_array,2)
            do j=1, size(data_array,2)
                v = data_array(:,i) - data_array(:,j)
                where(wraparound) v = v - nint(v)
                similarity_matrix(i,j) = sum(v**2)
            end do
        end do

    end function calculate_similarity_matrix








end module calculate_module
